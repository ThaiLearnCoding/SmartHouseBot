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

export const useVoiceAssistantStore = create((set) => ({
  messages: [],
  isRecording: false,
  isProcessing: false,
  currentTranscript: "",
  activeAudioUrl: null,
  error: null,

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
      set({
        error: getApiErrorMessage(error, "Failed to process text command."),
        isProcessing: false,
      });
    }
  },

  submitAudio: async (blob) => {
    set({ isProcessing: true, error: null });
    try {
      const result = await sendAudioTurn(blob);
      set((state) => ({
        messages: [
          ...state.messages,
          buildMessage("user", result.transcript || "Voice input", { transcriptOnly: true }),
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
      set({
        error: getApiErrorMessage(error, "Failed to process voice command."),
        isProcessing: false,
      });
    }
  },
}));
