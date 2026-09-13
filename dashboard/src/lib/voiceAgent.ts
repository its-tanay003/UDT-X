/**
 * UDT-X Voice Interaction & Voice Agent Controller.
 * 
 * Provides end-to-end voice control:
 * Audio Stream / VAD -> Web Speech Recognition -> Confidence / Ambiguity Filter
 * -> AI Copilot (Online/Offline) -> Verification & Action Dispatch -> Web Speech Synthesis (TTS)
 */

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

  public state: VoiceState = {
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    isSupported: false,
    interimTranscript: "",
    finalTranscript: "",
    confidence: 1.0,
    error: null,
    voiceTtsEnabled: true,
  };

  constructor() {
    this.initSpeechRecognition();
    this.initSpeechSynthesis();
  }

  private initSpeechRecognition() {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition ||
      (window as any).mozSpeechRecognition ||
      (window as any).msSpeechRecognition;

    if (!SpeechRecognition) {
      this.state.isSupported = false;
      this.state.error = "Web Speech API is not supported in this browser.";
      this.notify();
      return;
    }

    this.state.isSupported = true;
    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = "en-US";

      this.recognition.onstart = () => {
        this.state.isListening = true;
        this.state.error = null;
        this.state.interimTranscript = "";
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
        }
        this.notify();
      };

      this.recognition.onerror = (event: any) => {
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
      this.state.isSupported = false;
      this.state.error = e.message;
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
    if (!this.recognition) return;
    this.cancelSpeaking();

    this.state.interimTranscript = "";
    this.state.finalTranscript = "";
    this.state.error = null;

    try {
      this.recognition.start();
    } catch {
      // Already running
    }

    if (onFinal) {
      const checkFinal = (state: VoiceState) => {
        if (!state.isListening && state.finalTranscript) {
          this.listeners.delete(checkFinal);
          onFinal(state.finalTranscript, state.confidence);
        }
      };
      this.listeners.add(checkFinal);
    }
  }

  public stopListening() {
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
