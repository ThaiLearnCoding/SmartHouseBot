import { useState } from "react";
import AudioReplyPlayer from "./AudioReplyPlayer";
import ChatMessageList from "./ChatMessageList";
import VoiceRecorderButton from "./VoiceRecorderButton";

export default function VoiceChatPanel({
  messages,
  isRecording,
  isProcessing,
  currentTranscript,
  activeAudioUrl,
  error,
  onRecordingChange,
  onAudioReady,
  onSendText,
}) {
  const [text, setText] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const nextText = text.trim();
    if (!nextText) return;
    setText("");
    await onSendText(nextText);
  }

  return (
    <div className="card bg-base-100 shadow-sm">
      <div className="card-body gap-4">
        <div>
          <h2 className="card-title">Voice Assistant</h2>
          <p className="text-sm text-base-content/60">
            Nói hoặc nhập lệnh tiếng Việt để điều khiển nhà thông minh.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <VoiceRecorderButton
            isRecording={isRecording}
            isProcessing={isProcessing}
            onRecordingChange={onRecordingChange}
            onAudioReady={onAudioReady}
          />
          <span className="badge badge-outline">
            {isRecording ? "Đang nghe..." : isProcessing ? "Đang xử lý..." : "Sẵn sàng"}
          </span>
          {currentTranscript ? (
            <span className="text-sm text-base-content/60">Bạn đã nói: {currentTranscript}</span>
          ) : null}
        </div>

        <ChatMessageList messages={messages} isProcessing={isProcessing} />

        <form className="flex flex-col gap-3 md:flex-row" onSubmit={handleSubmit}>
          <input
            className="input input-bordered w-full"
            placeholder="Nhập lệnh, ví dụ: bật đèn, servo 90 độ..."
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <button type="submit" className="btn btn-outline" disabled={isProcessing}>
            Gửi
          </button>
        </form>

        {error ? <div className="alert alert-error">{error}</div> : null}
        <AudioReplyPlayer audioUrl={activeAudioUrl} />
      </div>
    </div>
  );
}
