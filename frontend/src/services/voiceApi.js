import { axiosInstance } from "../lib/axios";

export async function sendTextTurn(text) {
  const { data } = await axiosInstance.post("/voice/text-turn", { text });
  return data;
}

export async function sendAudioTurn(blob) {
  const formData = new FormData();
  formData.append("audio", blob, "voice.webm");

  const { data } = await axiosInstance.post("/voice/audio-turn", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
