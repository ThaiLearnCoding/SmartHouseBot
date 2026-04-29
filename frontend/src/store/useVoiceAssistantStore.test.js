import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/voiceApi", () => ({
  sendTextTurn: vi.fn(),
  sendAudioTurn: vi.fn(),
}));

import { sendAudioTurn, sendTextTurn } from "../services/voiceApi";
import { useVoiceAssistantStore } from "./useVoiceAssistantStore";

describe("useVoiceAssistantStore", () => {
  beforeEach(() => {
    useVoiceAssistantStore.setState({
      messages: [],
      isRecording: false,
      isProcessing: false,
      currentTranscript: "",
      activeAudioUrl: null,
      error: null,
    });
    vi.clearAllMocks();
  });

  it("ignores blank text submissions", async () => {
    await useVoiceAssistantStore.getState().submitText("   ");

    expect(sendTextTurn).not.toHaveBeenCalled();
    expect(useVoiceAssistantStore.getState().messages).toHaveLength(0);
  });

  it("adds user and assistant messages for text turns", async () => {
    sendTextTurn.mockResolvedValue({
      transcript: "bat den",
      intent: "set_led",
      response_text: "The LED is now on.",
      audio_url: "/audio/reply.wav",
    });

    await useVoiceAssistantStore.getState().submitText("bat den");

    const state = useVoiceAssistantStore.getState();
    expect(state.messages).toHaveLength(2);
    expect(state.messages[0].role).toBe("user");
    expect(state.messages[1].intent).toBe("set_led");
    expect(state.activeAudioUrl).toBe("/audio/reply.wav");
    expect(state.isProcessing).toBe(false);
  });

  it("stores text submission errors", async () => {
    sendTextTurn.mockRejectedValue(new Error("voice backend failed"));

    await useVoiceAssistantStore.getState().submitText("bat den");

    const state = useVoiceAssistantStore.getState();
    expect(state.error).toBe("voice backend failed");
    expect(state.isProcessing).toBe(false);
    expect(state.messages).toHaveLength(1);
  });

  it("adds transcript and assistant reply for audio turns", async () => {
    sendAudioTurn.mockResolvedValue({
      transcript: "doc nhiet do",
      intent: "read_sensor",
      response_text: "Current temperature is 28 degrees Celsius and humidity is 60 percent.",
      audio_url: "/audio/sensor.wav",
    });

    await useVoiceAssistantStore.getState().submitAudio(new Blob(["audio"]));

    const state = useVoiceAssistantStore.getState();
    expect(state.messages).toHaveLength(2);
    expect(state.messages[0].text).toBe("doc nhiet do");
    expect(state.messages[1].role).toBe("assistant");
    expect(state.currentTranscript).toBe("doc nhiet do");
  });

  it("stores audio submission errors", async () => {
    sendAudioTurn.mockRejectedValue(new Error("microphone upload failed"));

    await useVoiceAssistantStore.getState().submitAudio(new Blob(["audio"]));

    expect(useVoiceAssistantStore.getState().error).toBe("microphone upload failed");
    expect(useVoiceAssistantStore.getState().isProcessing).toBe(false);
  });
});
