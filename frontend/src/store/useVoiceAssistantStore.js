import { create } from "zustand";
import { getApiErrorMessage } from "../lib/axios";
import { sendAudioTurn, sendTextTurn } from "../services/voiceApi";

function buildMessage(role, text, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    ...extra,
  };
}

let voiceErrorTimeout = null;

export const useVoiceAssistantStore = create((set, get) => ({
  messages: [],
  isRecording: false,
  isProcessing: false,
  currentTranscript: "",
  activeAudioUrl: null,
  error: null,

  setError: (errorMsg) => {
    if (voiceErrorTimeout) clearTimeout(voiceErrorTimeout);
    set({ error: errorMsg });
    if (errorMsg) {
      voiceErrorTimeout = setTimeout(() => {
        set({ error: null });
      }, 5000);
    }
  },

  setRecording: (isRecording) => set({ isRecording }),

  submitText: async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    set((state) => ({
      messages: [...state.messages, buildMessage("user", trimmed)],
      currentTranscript: trimmed,
      isProcessing: true,
      error: null,
    }));
    if (voiceErrorTimeout) clearTimeout(voiceErrorTimeout);

    try {
      const result = await sendTextTurn(trimmed);
      set((state) => ({
        messages: [
          ...state.messages,
          buildMessage("assistant", result.response_text, {
            transcript: result.transcript,
            intent: result.intent,
            audioUrl: result.audio_url,
          }),
        ],
        activeAudioUrl: result.audio_url,
        isProcessing: false,
      }));
    } catch (error) {
      get().setError(getApiErrorMessage(error, "Failed to process text command."));
      set({ isProcessing: false });
    }
  },

  submitAudio: async (blob) => {
    const tempMessageId = `user-temp-${Date.now()}`;
    set((state) => ({ 
      messages: [...state.messages, { id: tempMessageId, role: "user", text: "[Đang phân tích lệnh...]" }],
      isProcessing: true, 
      error: null 
    }));
    if (voiceErrorTimeout) clearTimeout(voiceErrorTimeout);

    try {
      const result = await sendAudioTurn(blob);
      set((state) => ({
        messages: [
          ...state.messages.filter(m => m.id !== tempMessageId),
          buildMessage("user", result.transcript || "Invalid command...", { transcriptOnly: true }),
          buildMessage("assistant", result.response_text, {
            transcript: result.transcript,
            intent: result.intent,
            audioUrl: result.audio_url,
          }),
        ],
        currentTranscript: result.transcript,
        activeAudioUrl: result.audio_url,
        isProcessing: false,
      }));
    } catch (error) {
      set((state) => ({
        messages: state.messages.filter(m => m.id !== tempMessageId)
      }));
      get().setError(getApiErrorMessage(error, "Failed to process voice command."));
      set({ isProcessing: false });
    }
  },
}));
