import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/voiceApi", () => ({
  transcribeAudio: vi.fn(),
}));

import { transcribeAudio } from "../services/voiceApi";
import { useVoiceAssistantStore } from "./useVoiceAssistantStore";

class MockWebSocket {
  static lastInstance = null;

  constructor(url) {
    this.url = url;
    this.readyState = 1;
    MockWebSocket.lastInstance = this;
    queueMicrotask(() => this.onopen?.());
  }

  send(data) {
    this.lastPayload = JSON.parse(data);
    queueMicrotask(() => {
      this.onmessage?.({
        data: JSON.stringify({
          type: "assistant_done",
          intent: "set_led",
          response_text: "The LED is now on.",
          transcript: this.lastPayload.text,
        }),
      });
    });
  }

  close() {}
}

describe("useVoiceAssistantStore", () => {
  beforeEach(() => {
    globalThis.WebSocket = MockWebSocket;
    globalThis.window = {
      location: {
        protocol: "http:",
        host: "localhost:5173",
      },
    };

    useVoiceAssistantStore.setState({
      messages: [],
      isRecording: false,
      isProcessing: false,
      currentTranscript: "",
      audioChunks: [],
      error: null,
    });
    vi.clearAllMocks();
    MockWebSocket.lastInstance = null;
  });

  it("ignores blank text submissions", async () => {
    await useVoiceAssistantStore.getState().submitText("   ");

    expect(MockWebSocket.lastInstance).toBeNull();
    expect(useVoiceAssistantStore.getState().messages).toHaveLength(0);
  });

  it("adds user and assistant messages for text turns", async () => {
    await useVoiceAssistantStore.getState().submitText("bat den");
    await vi.waitFor(() => {
      expect(useVoiceAssistantStore.getState().messages.length).toBeGreaterThanOrEqual(2);
    });

    const state = useVoiceAssistantStore.getState();
    expect(state.messages[0].role).toBe("user");
    expect(state.messages[1].role).toBe("assistant");
    expect(MockWebSocket.lastInstance?.url).toBe("ws://localhost:5173/api/voice/stream");
  });

  it("stores text submission errors", async () => {
    globalThis.WebSocket = class FailingWebSocket {
      constructor() {
        queueMicrotask(() => this.onerror?.());
      }
    };

    await useVoiceAssistantStore.getState().submitText("bat den");

    const state = useVoiceAssistantStore.getState();
    expect(state.error).toBeTruthy();
    expect(state.isProcessing).toBe(false);
    expect(state.messages).toHaveLength(1);
  });

  it("adds transcript and assistant reply for audio turns", async () => {
    transcribeAudio.mockResolvedValue({ transcript: "doc nhiet do" });

    await useVoiceAssistantStore.getState().submitAudio(new Blob(["audio"]));
    await vi.waitFor(() => {
      expect(useVoiceAssistantStore.getState().messages.length).toBeGreaterThanOrEqual(2);
    });

    const state = useVoiceAssistantStore.getState();
    expect(state.messages[0].text).toBe("doc nhiet do");
    expect(state.messages[1].role).toBe("assistant");
    expect(state.currentTranscript).toBe("doc nhiet do");
  });

  it("stores audio submission errors", async () => {
    transcribeAudio.mockRejectedValue(new Error("microphone upload failed"));

    await useVoiceAssistantStore.getState().submitAudio(new Blob(["audio"]));

    expect(useVoiceAssistantStore.getState().error).toBe("microphone upload failed");
    expect(useVoiceAssistantStore.getState().isProcessing).toBe(false);
  });
});
