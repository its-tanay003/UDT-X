import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Bot,
  Send,
  X,
  Sparkles,
  Shield,
  Radio,
  Zap,
  CheckCircle,
  AlertTriangle,
  Compass,
  ArrowRight,
  WifiOff,
  Wifi,
  Lock,
  RotateCcw,
  Check,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
} from "lucide-react";
import { useAuthStore } from "../lib/auth";
import { useLiveStore } from "../lib/store";
import { OfflineCopilotEngine } from "../lib/offlineCopilot";
import type { OfflineActionStage } from "../lib/offlineCopilot";
import { globalVoiceController, type VoiceState } from "../lib/voiceAgent";

interface CopilotMessage {
  id: string;
  sender: "user" | "copilot";
  text: string;
  spokenText?: string;
  timestamp: string;
  isOffline?: boolean;
  intent?: string;
  actionResult?: any;
  suggestedRoutes?: string[];
  recommendations?: Array<{
    id: string;
    title: string;
    reasoning: string;
    target_route: string;
    badge: string;
  }>;
  confirmationPayload?: {
    action_id: string;
    parameters: Record<string, any>;
    prompt: string;
    target_route?: string;
  };
}

export const CopilotModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, accessToken } = useAuthStore();
  const { isConnected } = useLiveStore();

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([
    {
      id: "init_1",
      sender: "copilot",
      text: `Greetings Operator ${user?.display_name || "Analyst"}. I am UDT-X Sentinel, your deeply integrated mission-control voice & text copilot. You can speak naturally or type to navigate between consoles, filter active anomalies, simulate attack vectors, or explain mathematical detection models.`,
      spokenText: `Greetings Operator ${user?.display_name || "Analyst"}. Sentinel copilot standing by.`,
      timestamp: new Date().toLocaleTimeString(),
      suggestedRoutes: ["/app/monitor", "/app/incidents", "/app/threats", "/app/replay"],
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [stagedActions, setStagedActions] = useState<OfflineActionStage[]>([]);
  const [voiceState, setVoiceState] = useState<VoiceState>(globalVoiceController.state);
  const [pendingConfirmation, setPendingConfirmation] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsub = globalVoiceController.subscribe((st) => {
      setVoiceState(st);
    });
    return unsub;
  }, []);

  useEffect(() => {
    setStagedActions(OfflineCopilotEngine.getStagedActions());
    if (!isOpen) {
      globalVoiceController.stopListening();
      globalVoiceController.cancelSpeaking();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, voiceState.interimTranscript]);

  if (!isOpen) return null;

  const handleSend = async (customQuery?: string, isFromVoice: boolean = false) => {
    const q = (customQuery || input).trim();
    if (!q) return;

    // Check if user is confirming or cancelling a pending action via voice
    if (pendingConfirmation) {
      const lower = q.toLowerCase();
      if (lower.includes("confirm") || lower.includes("authorize") || lower.includes("proceed") || lower.includes("yes")) {
        setInput("");
        await handleConfirmAction(pendingConfirmation, isFromVoice);
        setPendingConfirmation(null);
        return;
      }
      if (lower.includes("cancel") || lower.includes("abort") || lower.includes("no") || lower.includes("stop")) {
        setInput("");
        setPendingConfirmation(null);
        setMessages((prev) => [
          ...prev,
          {
            id: `usr_${Date.now()}`,
            sender: "user",
            text: q,
            timestamp: new Date().toLocaleTimeString(),
          },
          {
            id: `cop_cancel_${Date.now()}`,
            sender: "copilot",
            text: "Sensitive action was cancelled by operator.",
            spokenText: "Action cancelled.",
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
        if (voiceState.voiceTtsEnabled) {
          globalVoiceController.speak("Action cancelled.");
        }
        return;
      }
    }

    const userMsg: CopilotMessage = {
      id: `usr_${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customQuery) setInput("");
    setIsLoading(true);

    // Online execution with FastAPI Core API
    if (isConnected && navigator.onLine) {
      try {
        const res = await fetch("http://localhost:8000/copilot/query", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            query: q,
            current_route: location.pathname,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          const spoken = data.spoken_response || data.message;
          const copilotMsg: CopilotMessage = {
            id: `cop_${Date.now()}`,
            sender: "copilot",
            text: data.message,
            spokenText: spoken,
            timestamp: new Date().toLocaleTimeString(),
            isOffline: false,
            intent: data.intent,
            actionResult: data.executed_action_result,
            suggestedRoutes: data.suggested_routes,
            recommendations: data.recommendations,
            confirmationPayload: data.requires_user_confirmation
              ? data.confirmation_payload
              : undefined,
          };

          if (data.requires_user_confirmation) {
            setPendingConfirmation(data.confirmation_payload);
          }

          setMessages((prev) => [...prev, copilotMsg]);

          // Trigger voice response if enabled or invoked via voice
          if (voiceState.voiceTtsEnabled && spoken) {
            globalVoiceController.speak(spoken);
          }

          // Handle automatic verified client navigation if tool was executed
          if (data.tool_call?.tool_name === "navigate_page" && data.tool_call.target_route) {
            navigate(data.tool_call.target_route);
          } else if (data.tool_call?.tool_name === "filter_alerts" && data.tool_call.target_route) {
            navigate(data.tool_call.target_route);
          }
          setIsLoading(false);
          return;
        }
      } catch (err) {
        // Fall through to offline engine
      }
    }

    // Offline / Air-Gapped Fallback Engine
    const offlineRes = OfflineCopilotEngine.processQuery(
      q,
      user?.role || "analyst",
      user?.display_name || "Analyst",
      user?.email || "analyst@udtx.local",
      location.pathname
    );

    const spoken = offlineRes.spoken_response || offlineRes.message;
    const copilotOfflineMsg: CopilotMessage = {
      id: `cop_${Date.now()}`,
      sender: "copilot",
      text: offlineRes.message,
      spokenText: spoken,
      timestamp: new Date().toLocaleTimeString(),
      isOffline: true,
      intent: offlineRes.intent,
      suggestedRoutes: offlineRes.suggested_routes,
      recommendations: offlineRes.recommendations,
      confirmationPayload: offlineRes.requires_user_confirmation
        ? offlineRes.confirmation_payload
        : undefined,
    };

    if (offlineRes.requires_user_confirmation) {
      setPendingConfirmation(offlineRes.confirmation_payload);
    }

    setMessages((prev) => [...prev, copilotOfflineMsg]);

    if (voiceState.voiceTtsEnabled && spoken) {
      globalVoiceController.speak(spoken);
    }

    if (offlineRes.tool_call?.tool_name === "navigate_page" && offlineRes.tool_call.target_route) {
      navigate(offlineRes.tool_call.target_route);
    }
    if (offlineRes.staged_action) {
      setStagedActions(OfflineCopilotEngine.getStagedActions());
    }

    setIsLoading(false);
  };

  const handleConfirmAction = async (payload: any, isFromVoice: boolean = false) => {
    setIsLoading(true);
    setPendingConfirmation(null);

    if (isConnected && navigator.onLine) {
      try {
        const res = await fetch("http://localhost:8000/copilot/query", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            query: `Confirm ${payload.action_id}`,
            current_route: location.pathname,
            action_request: {
              action_id: payload.action_id,
              parameters: payload.parameters,
              confirmed: true,
            },
          }),
        });

        if (res.ok) {
          const data = await res.json();
          const spoken = data.spoken_response || `Action ${payload.action_id} executed.`;
          setMessages((prev) => [
            ...prev,
            {
              id: `cop_conf_${Date.now()}`,
              sender: "copilot",
              text: data.message,
              spokenText: spoken,
              timestamp: new Date().toLocaleTimeString(),
              isOffline: false,
              actionResult: data.executed_action_result,
              suggestedRoutes: data.suggested_routes,
            },
          ]);

          if (voiceState.voiceTtsEnabled && spoken) {
            globalVoiceController.speak(spoken);
          }

          if (payload.target_route) {
            navigate(payload.target_route);
          }
          setIsLoading(false);
          return;
        }
      } catch {}
    }

    // Offline confirmation
    const offlineSpoken = `Action ${payload.action_id} executed locally.`;
    setMessages((prev) => [
      ...prev,
      {
        id: `cop_conf_${Date.now()}`,
        sender: "copilot",
        text: `Offline Action Confirmed: Executing ${payload.action_id} locally.`,
        spokenText: offlineSpoken,
        timestamp: new Date().toLocaleTimeString(),
        isOffline: true,
      },
    ]);

    if (voiceState.voiceTtsEnabled) {
      globalVoiceController.speak(offlineSpoken);
    }

    if (payload.target_route) {
      navigate(payload.target_route);
    }
    setIsLoading(false);
  };

  const toggleListening = () => {
    if (voiceState.isListening) {
      globalVoiceController.stopListening();
    } else {
      globalVoiceController.startListening((transcript, confidence) => {
        if (confidence < 0.35) {
          // Low confidence ambiguity check
          setMessages((prev) => [
            ...prev,
            {
              id: `cop_ambig_${Date.now()}`,
              sender: "copilot",
              text: "Speech recognition confidence was low. Could you please repeat or clarify your command?",
              spokenText: "I couldn't hear that clearly. Please repeat your command.",
              timestamp: new Date().toLocaleTimeString(),
            },
          ]);
          if (voiceState.voiceTtsEnabled) {
            globalVoiceController.speak("I couldn't hear that clearly. Please repeat your command.");
          }
          return;
        }
        handleSend(transcript, true);
      });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-[#0B1220]/80 backdrop-blur-md animate-fade-in font-mono">
      <div className="w-full max-w-2xl h-[640px] rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/30 shadow-[0_0_50px_rgba(63,199,212,0.2)] flex flex-col overflow-hidden relative">
        {/* Modal Top Banner */}
        <div className="p-4 bg-[#0B1220] border-b border-[#3FC7D4]/20 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center text-[#3FC7D4] shadow-[0_0_15px_rgba(63,199,212,0.3)]">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-sm text-[#E7ECF5] tracking-wider">
                  UDT-X SENTINEL COPILOT
                </span>
                {isConnected ? (
                  <span className="px-2 py-0.5 rounded text-[10px] bg-[#4CAF7D]/15 border border-[#4CAF7D]/30 text-[#4CAF7D] font-bold flex items-center gap-1">
                    <Wifi className="w-3 h-3" />
                    <span>ONLINE API</span>
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] bg-[#FF8A3D]/15 border border-[#FF8A3D]/30 text-[#FF8A3D] font-bold flex items-center gap-1 animate-pulse">
                    <WifiOff className="w-3 h-3" />
                    <span>OFFLINE RAG</span>
                  </span>
                )}
                <span className="px-2 py-0.5 rounded text-[10px] bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] font-bold flex items-center gap-1">
                  <Mic className="w-3 h-3" />
                  <span>VOICE ACTIVE</span>
                </span>
              </div>
              <p className="text-[10px] text-[#8A95AA]">
                Voice & Text Autonomous Enclave Copilot & Telemetry Agent
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* TTS Voice Toggle */}
            <button
              onClick={() => globalVoiceController.setTtsEnabled(!voiceState.voiceTtsEnabled)}
              title={voiceState.voiceTtsEnabled ? "Disable Voice Output (Mute)" : "Enable Voice Output (TTS)"}
              className={`p-1.5 rounded-lg border transition-colors ${
                voiceState.voiceTtsEnabled
                  ? "bg-[#3FC7D4]/20 border-[#3FC7D4]/50 text-[#3FC7D4]"
                  : "bg-[#131B2E] border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5]"
              }`}
            >
              {voiceState.voiceTtsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] hover:border-[#3FC7D4] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages Stream Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
            >
              <div className="flex items-center gap-2 mb-1 text-[10px] text-[#8A95AA]">
                <span>{m.sender === "user" ? user?.display_name || "Analyst" : "UDT-X Sentinel"}</span>
                <span>•</span>
                <span>{m.timestamp}</span>
                {m.isOffline && (
                  <span className="text-[#FF8A3D] font-bold">[OFFLINE RAG]</span>
                )}
                {m.sender === "copilot" && voiceState.voiceTtsEnabled && (
                  <button
                    onClick={() => m.spokenText && globalVoiceController.speak(m.spokenText)}
                    title="Replay Voice Audio"
                    className="hover:text-[#3FC7D4] transition-colors"
                  >
                    <Volume2 className="w-3 h-3 inline" />
                  </button>
                )}
              </div>

              <div
                className={`p-3.5 rounded-xl max-w-[85%] leading-relaxed ${
                  m.sender === "user"
                    ? "bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 text-[#E7ECF5]"
                    : "bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5]"
                }`}
              >
                <div>{m.text}</div>

                {/* Confirmation Action Gate */}
                {m.confirmationPayload && (
                  <div className="mt-3 p-3 rounded-lg bg-[#FF8A3D]/10 border border-[#FF8A3D]/30 space-y-2">
                    <div className="flex items-center gap-2 text-[#FF8A3D] font-bold text-xs">
                      <Lock className="w-4 h-4" />
                      <span>SENSITIVE OPERATION AUTHORIZATION</span>
                    </div>
                    <div className="text-[11px] text-[#E7ECF5]">
                      {m.confirmationPayload.prompt}
                    </div>
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => handleConfirmAction(m.confirmationPayload)}
                        className="px-3 py-1 rounded bg-[#FF8A3D] hover:bg-[#E0742B] text-[#0B1220] font-bold text-[11px] flex items-center gap-1 shadow-md transition-all active:scale-[0.97]"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>AUTHORIZE & EXECUTE</span>
                      </button>
                      <button
                        onClick={() => {
                          setPendingConfirmation(null);
                          setMessages((prev) => [
                            ...prev,
                            {
                              id: `cop_cancel_${Date.now()}`,
                              sender: "copilot",
                              text: "Operation cancelled by operator.",
                              spokenText: "Operation cancelled.",
                              timestamp: new Date().toLocaleTimeString(),
                            },
                          ]);
                        }}
                        className="px-3 py-1 rounded bg-[#131B2E] border border-[#FF8A3D]/30 text-[#8A95AA] hover:text-[#E7ECF5] text-[11px]"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Suggested Action Routes */}
                {m.suggestedRoutes && m.suggestedRoutes.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-[#3FC7D4]/10 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-[#8A95AA]">QUICK PIVOT:</span>
                    {m.suggestedRoutes.map((r) => (
                      <button
                        key={r}
                        onClick={() => {
                          navigate(r);
                          onClose();
                        }}
                        className="px-2 py-0.5 rounded bg-[#131B2E] border border-[#3FC7D4]/30 hover:border-[#3FC7D4] text-[#3FC7D4] text-[10px] font-bold transition-all flex items-center gap-1"
                      >
                        <span>{r}</span>
                        <span>→</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Personalized Recommendations */}
                {m.recommendations && m.recommendations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-[#3FC7D4]/15 space-y-1.5">
                    <div className="text-[10px] text-[#3FC7D4] font-bold flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      <span>PERSONALIZED SHIFT RECOMMENDATIONS:</span>
                    </div>
                    <div className="space-y-1">
                      {m.recommendations.map((rec) => (
                        <div
                          key={rec.id}
                          onClick={() => {
                            navigate(rec.target_route);
                            onClose();
                          }}
                          className="p-2 rounded bg-[#131B2E] hover:bg-[#1B2540] border border-[#3FC7D4]/20 hover:border-[#3FC7D4]/50 transition-all cursor-pointer flex items-center justify-between group"
                        >
                          <div>
                            <div className="text-[#E7ECF5] font-bold text-[11px] group-hover:text-[#3FC7D4] transition-colors">
                              {rec.title}
                            </div>
                            <div className="text-[9px] text-[#8A95AA]">{rec.reasoning}</div>
                          </div>
                          <ArrowRight className="w-3.5 h-3.5 text-[#3FC7D4] group-hover:translate-x-1 transition-transform shrink-0" />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-[#3FC7D4] text-xs">
              <span className="w-3 h-3 rounded-full border border-[#3FC7D4] border-t-transparent animate-spin" />
              <span>Sentinel evaluating telemetry context & permissions...</span>
            </div>
          )}

          {/* Realtime Live Speech Waveform & Interim Transcription Banner */}
          {voiceState.isListening && (
            <div className="p-3 rounded-xl bg-[#3FC7D4]/10 border border-[#3FC7D4]/40 flex items-center gap-3 animate-pulse">
              <div className="flex items-center gap-1">
                <span className="w-1 h-3 bg-[#3FC7D4] rounded-full animate-bounce" />
                <span className="w-1 h-5 bg-[#3FC7D4] rounded-full animate-bounce [animation-delay:0.15s]" />
                <span className="w-1 h-4 bg-[#3FC7D4] rounded-full animate-bounce [animation-delay:0.3s]" />
                <span className="w-1 h-6 bg-[#3FC7D4] rounded-full animate-bounce [animation-delay:0.45s]" />
              </div>
              <div className="flex-1">
                <div className="text-[10px] font-bold text-[#3FC7D4]">LISTENING FOR VOICE COMMAND...</div>
                <div className="text-xs text-[#E7ECF5] italic">
                  {voiceState.interimTranscript || "Speak now (e.g. 'Open live monitor', 'Explain TreeSHAP math')..."}
                </div>
              </div>
              <button
                onClick={() => globalVoiceController.stopListening()}
                className="px-2 py-1 rounded bg-[#FF4757]/20 border border-[#FF4757]/40 text-[#FF4757] text-[10px] font-bold"
              >
                Stop
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Bottom Suggested Prompt Quick Chips */}
        <div className="px-4 py-2 bg-[#0B1220]/70 border-t border-[#3FC7D4]/10 flex flex-wrap items-center gap-2 text-[10px]">
          <span className="text-[#8A95AA]">VOICE / TEXT CHIPS:</span>
          {[
            "Take me to Live Monitor",
            "Show critical alerts",
            "Simulate a DDoS attack",
            "Explain TreeSHAP math",
            "What is our composite risk?",
          ].map((chip) => (
            <button
              key={chip}
              onClick={() => handleSend(chip)}
              className="px-2 py-0.5 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#3FC7D4] hover:border-[#3FC7D4]/40 transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Textarea & Voice Microphone Bar */}
        <div className="p-3 bg-[#0B1220] border-t border-[#3FC7D4]/20 flex items-center gap-2">
          {/* Push-to-Talk Microphone Button */}
          <button
            onClick={toggleListening}
            title={voiceState.isListening ? "Stop Listening" : "Start Voice Command"}
            className={`p-2.5 rounded-xl border transition-all flex items-center justify-center shrink-0 ${
              voiceState.isListening
                ? "bg-[#FF4757] border-[#FF4757] text-white shadow-[0_0_15px_rgba(255,71,87,0.5)] animate-pulse"
                : "bg-[#131B2E] hover:bg-[#1B2540] border-[#3FC7D4]/30 text-[#3FC7D4] hover:border-[#3FC7D4]"
            }`}
          >
            {voiceState.isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={
              voiceState.isListening
                ? "Listening to voice input..."
                : "Ask Sentinel or click mic (e.g., 'Open live stream', 'Simulate attack', 'Explain data diode')..."
            }
            className="flex-1 bg-[#131B2E] border border-[#3FC7D4]/25 rounded-xl px-3.5 py-2.5 text-xs text-[#E7ECF5] placeholder-[#8A95AA]/60 focus:outline-none focus:border-[#3FC7D4]"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="p-2.5 rounded-xl bg-[#3FC7D4] hover:bg-[#35B2BE] text-[#0B1220] font-bold transition-all disabled:opacity-40 active:scale-[0.95] flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
