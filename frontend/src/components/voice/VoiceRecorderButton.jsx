import { useRef } from "react";

export default function VoiceRecorderButton({ isRecording, isProcessing, onRecordingChange, onAudioReady }) {
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia) {
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    chunksRef.current = [];

    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      streamRef.current?.getTracks().forEach((track) => track.stop());
      onRecordingChange(false);
      await onAudioReady(blob);
    };
    recorder.start();
    onRecordingChange(true);
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  }

  return (
    <button
      type="button"
      className="bmw-button-primary"
      style={isRecording ? { backgroundColor: 'var(--color-error)' } : {}}
      disabled={isProcessing}
      onClick={isRecording ? stopRecording : startRecording}
    >
      {isRecording ? "Dừng ghi âm" : "Bắt đầu ghi âm"}
    </button>
  );
}
