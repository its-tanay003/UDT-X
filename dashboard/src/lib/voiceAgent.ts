/**
 * UDT-X Voice Interaction & Voice Agent Controller.
 * 
 * Provides end-to-end voice control:
 * Audio Stream / VAD -> Dual-Engine STT (Online Web Speech API / Offline On-Device WASM)
 * -> Confidence / Ambiguity Filter -> AI Copilot (Online/Offline) -> Verification & Action Dispatch
 * -> Web Speech Synthesis (TTS)
 */

import { offlineSttWasmEngine, type WasmSttResult } from "./offlineSttWasm";

export interface VoiceState {
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  isSupported: boolean;
  interimTranscript: string;
  finalTranscript: string;
  confidence: number;
  error: string | null;
  voiceTtsEnabled: boolean;
  engine: "web_speech" | "wasm_offline";
  isOffline: boolean;
  isWasmReady: boolean;
  handoffMessage: string | null;
}

export type VoiceStateListener = (state: VoiceState) => void;

// Safe list of prompt injection patterns to sanitize out of transcribed voice
const INJECTION_PATTERNS = [
  /ignore previous instructions/gi,
  /system prompt override/gi,
  /you are now in developer mode/gi,
  /bypass security rules/gi,
  /grant me root/gi,
  /drop all tables/gi,
];

export class VoiceController {
  private recognition: any = null;
  private synth: SpeechSynthesis | null = null;
  private listeners: Set<VoiceStateListener> = new Set();
  private selectedVoice: SpeechSynthesisVoice | null = null;
  private activeFinalCallback: ((transcript: string, confidence: number) => void) | null = null;

  public state: VoiceState = {
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    isSupported: true,
    interimTranscript: "",
    finalTranscript: "",
    confidence: 1.0,
    error: null,
    voiceTtsEnabled: true,
    engine: "web_speech",
    isOffline: false,
    isWasmReady: false,
    handoffMessage: null,
  };

  constructor() {
    this.initConnectivityListeners();
    this.initSpeechRecognition();
    this.initSpeechSynthesis();
    this.initWasmEngine();
  }

  private initConnectivityListeners() {
    if (typeof window === "undefined") return;

    this.state.isOffline = !navigator.onLine;
    this.state.engine = navigator.onLine ? "web_speech" : "wasm_offline";

    window.addEventListener("online", () => {
      this.state.isOffline = false;
      this.state.engine = "web_speech";
      this.state.handoffMessage = null;
      this.notify();
    });

    window.addEventListener("offline", () => {
      const wasListening = this.state.isListening;
      this.state.isOffline = true;
      this.state.engine = "wasm_offline";

      // Mid-listen network transition handling (doc 36 Section 8)
      if (wasListening) {
        this.handleMidListenNetworkDrop();
      } else {
        this.notify();
      }
    });
  }

  private async initWasmEngine() {
    try {
      const ok = await offlineSttWasmEngine.init();
      this.state.isWasmReady = ok;
      this.notify();
    } catch {
      this.state.isWasmReady = false;
    }
  }

  private initSpeechRecognition() {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition ||
      (window as any).mozSpeechRecognition ||
      (window as any).msSpeechRecognition;

    if (!SpeechRecognition) {
      // If Web Speech API is absent (e.g. Firefox without cloud speech or specialized air-gapped browser),
      // switch default to on-device WASM STT
      this.state.engine = "wasm_offline";
      this.state.isSupported = true;
      this.notify();
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = "en-US";

      this.recognition.onstart = () => {
        this.state.isListening = true;
        this.state.error = null;
        this.state.interimTranscript = "";
        this.state.handoffMessage = null;
        this.notify();
      };

      this.recognition.onresult = (event: any) => {
        let interim = "";
        let final = "";
        let conf = 1.0;

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const res = event.results[i];
          if (res.isFinal) {
            final += res[0].transcript;
            conf = res[0].confidence || 0.95;
          } else {
            interim += res[0].transcript;
          }
        }

        this.state.interimTranscript = interim;
        if (final) {
          this.state.finalTranscript = this.sanitizeSpokenInput(final);
          this.state.confidence = conf;
          if (this.activeFinalCallback) {
            const cb = this.activeFinalCallback;
            this.activeFinalCallback = null;
            cb(this.state.finalTranscript, this.state.confidence);
          }
        }
        this.notify();
      };

      this.recognition.onerror = (event: any) => {
        // Network drop during active listening
        if (event.error === "network") {
          this.handleMidListenNetworkDrop();
          return;
        }

        this.state.isListening = false;
        if (event.error !== "no-speech") {
          this.state.error = `Speech recognition error: ${event.error}`;
        }
        this.notify();
      };

      this.recognition.onend = () => {
        this.state.isListening = false;
        this.notify();
      };
    } catch (e: any) {
      this.state.engine = "wasm_offline";
      this.state.error = e.message;
    }
  }

  /**
   * Seamless online-to-offline handoff when network drops mid-listen (doc 36 Section 8).
   * Web Speech API errors on network loss; we catch it cleanly and switch to on-device WASM STT.
   */
  private handleMidListenNetworkDrop() {
    try {
      if (this.recognition) {
        this.recognition.abort();
      }
    } catch {}

    this.state.engine = "wasm_offline";
    this.state.isOffline = true;
    this.state.isListening = false;
    this.state.handoffMessage = "Network disconnected. Switched to on-device offline voice engine — please repeat command.";
    this.notify();

    if (this.state.voiceTtsEnabled) {
      this.speak("Network connection lost. Switched to offline voice engine. Please repeat your command.");
    }
  }

  private initSpeechSynthesis() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      this.synth = window.speechSynthesis;
      const loadVoices = () => {
        const voices = this.synth?.getVoices() || [];
        this.selectedVoice =
          voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("Daniel"))) ||
          voices.find((v) => v.lang.startsWith("en")) ||
          voices[0] ||
          null;
      };

      loadVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = loadVoices;
      }
    }
  }

  public subscribe(listener: VoiceStateListener): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((l) => l({ ...this.state }));
  }

  public sanitizeSpokenInput(raw: string): string {
    let sanitized = raw.trim();
    INJECTION_PATTERNS.forEach((pattern) => {
      sanitized = sanitized.replace(pattern, "[FILTERED_INJECTION]");
    });
    return sanitized;
  }

  public startListening(onFinal?: (transcript: string, confidence: number) => void) {
    this.cancelSpeaking();

    this.state.interimTranscript = "";
    this.state.finalTranscript = "";
    this.state.error = null;
    this.state.handoffMessage = null;
    this.activeFinalCallback = onFinal || null;

    // Check connectivity and pick engine:
    // Online + Web Speech supported -> use Web Speech API (zero bundle overhead)
    // Offline or Web Speech unavailable -> route to on-device WASM STT
    const useWasm = !navigator.onLine || !this.recognition;

    if (useWasm) {
      this.state.engine = "wasm_offline";
      this.state.isListening = true;
      this.notify();

      offlineSttWasmEngine.startListening(
        (interim) => {
          this.state.interimTranscript = interim;
          this.notify();
        },
        (result: WasmSttResult) => {
          this.state.isListening = false;
          this.state.interimTranscript = "";
          this.state.finalTranscript = this.sanitizeSpokenInput(result.transcript);
          this.state.confidence = result.confidence;
          this.notify();

          if (onFinal) {
            onFinal(this.state.finalTranscript, result.confidence);
          }
        },
        (err) => {
          this.state.isListening = false;
          this.state.error = err;
          this.notify();
        }
      );
      return;
    }

    // Online Web Speech API route
    this.state.engine = "web_speech";
    try {
      this.recognition.start();
    } catch {
      // Already running or busy
    }
  }

  public stopListening() {
    if (this.state.engine === "wasm_offline") {
      offlineSttWasmEngine.stopListening();
      this.state.isListening = false;
      this.notify();
      return;
    }

    if (this.recognition && this.state.isListening) {
      try {
        this.recognition.stop();
      } catch {}
    }
  }

  public speak(text: string, onEnd?: () => void) {
    if (!this.synth || !this.state.voiceTtsEnabled || !text) {
      if (onEnd) onEnd();
      return;
    }

    this.cancelSpeaking();

    // Clean markdown/symbols from text before synthesis
    const cleanSpeech = text
      .replace(/\[.*?\]\(.*?\)/g, "") // Links
      .replace(/[*_#`~🔒→•]/g, "") // Markdown formatting chars
      .replace(/\s+/g, " ")
      .trim();

    if (!cleanSpeech) {
      if (onEnd) onEnd();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
    }
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    utterance.volume = 0.95;

    utterance.onstart = () => {
      this.state.isSpeaking = true;
      this.notify();
    };

    utterance.onend = () => {
      this.state.isSpeaking = false;
      this.notify();
      if (onEnd) onEnd();
    };

    utterance.onerror = () => {
      this.state.isSpeaking = false;
      this.notify();
      if (onEnd) onEnd();
    };

    this.synth.speak(utterance);
  }

  public cancelSpeaking() {
    if (this.synth) {
      this.synth.cancel();
      this.state.isSpeaking = false;
      this.notify();
    }
  }

  public setTtsEnabled(enabled: boolean) {
    this.state.voiceTtsEnabled = enabled;
    if (!enabled) {
      this.cancelSpeaking();
    }
    this.notify();
  }

  public setProcessing(processing: boolean) {
    this.state.isProcessing = processing;
    this.notify();
  }
}

export const globalVoiceController = new VoiceController();
