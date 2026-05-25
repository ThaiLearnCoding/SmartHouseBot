import { create } from "zustand";
import { getApiErrorMessage } from "../lib/axios";
import { transcribeAudio } from "../services/voiceApi";

function buildMessage(role, text, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    ...extra,
  };
}

let voiceErrorTimeout = null;
let voiceSocket = null;
let connectPromise = null;

export const useVoiceAssistantStore = create((set, get) => ({
  messages: [],
  isRecording: false,
  isProcessing: false,
  currentTranscript: "",
  audioChunks: [],
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

  ensureSocket: () => {
    if (voiceSocket && voiceSocket.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }
    if (connectPromise) return connectPromise;

    connectPromise = new Promise((resolve, reject) => {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const host = window.location.hostname;
      const port = window.location.port && window.location.port !== "8000" ? "8000" : window.location.port;
      const wsUrl = `${protocol}://${host}${port ? `:${port}` : ""}/api/voice/stream`;
      voiceSocket = new WebSocket(wsUrl);

      voiceSocket.onopen = () => {
        connectPromise = null;
        resolve();
      };

      voiceSocket.onerror = () => {
        connectPromise = null;
        reject(new Error("WebSocket connection failed"));
      };

      voiceSocket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        const { type } = payload;
        if (type === "assistant_token") {
          set((state) => {
            const messages = state.messages.map((message) => {
              if (message.role !== "assistant" || !message.isStreaming) return message;
              return { ...message, text: `${message.text}${payload.token}` };
            });
            return { messages };
          });
        }

        if (type === "assistant_done") {
          set((state) => {
            const messages = state.messages.map((message) => {
              if (message.role !== "assistant" || !message.isStreaming) return message;
              return {
                ...message,
                isStreaming: false,
                intent: payload.intent,
              };
            });
            return { messages, isProcessing: false };
          });
        }

        if (type === "audio_chunk") {
          set((state) => ({ audioChunks: [...state.audioChunks, payload.data] }));
        }
      };

      voiceSocket.onclose = () => {
        voiceSocket = null;
        set({ isProcessing: false });
      };
    });

    return connectPromise;
  },

  removePlayedChunk: () => {
    set((state) => ({ audioChunks: state.audioChunks.slice(1) }));
  },

  submitText: async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    set((state) => ({
      messages: [...state.messages, buildMessage("user", trimmed)],
      currentTranscript: trimmed,
      isProcessing: true,
      audioChunks: [],
      error: null,
    }));
    if (voiceErrorTimeout) clearTimeout(voiceErrorTimeout);

    try {
      await get().ensureSocket();
      set((state) => ({
        messages: [
          ...state.messages,
          { id: `assistant-${Date.now()}`, role: "assistant", text: "", isStreaming: true },
        ],
      }));
      voiceSocket.send(JSON.stringify({ type: "user_text", text: trimmed }));
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
      audioChunks: [],
      error: null
    }));
    if (voiceErrorTimeout) clearTimeout(voiceErrorTimeout);

    try {
      const result = await transcribeAudio(blob);
      const transcript = result.transcript || "";
      set((state) => ({
        messages: [
          ...state.messages.filter(m => m.id !== tempMessageId),
          buildMessage("user", transcript || "Invalid command...", { transcriptOnly: true }),
          { id: `assistant-${Date.now()}`, role: "assistant", text: "", isStreaming: true },
        ],
        currentTranscript: transcript,
      }));

      await get().ensureSocket();
      voiceSocket.send(JSON.stringify({ type: "user_text", text: transcript }));
    } catch (error) {
      set((state) => ({
        messages: state.messages.filter(m => m.id !== tempMessageId)
      }));
      get().setError(getApiErrorMessage(error, "Failed to process voice command."));
      set({ isProcessing: false });
    }
  },
}));
