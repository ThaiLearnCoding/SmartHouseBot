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
    <div className="bmw-card" style={{ border: '1px solid var(--color-hairline)' }}>
      <div className="bmw-card-header">
        <h2 className="bmw-card-title">Voice Assistant</h2>
        <p className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>
          Nói hoặc nhập lệnh tiếng Việt để điều khiển nhà thông minh.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-center gap-4">
          <VoiceRecorderButton
            isRecording={isRecording}
            isProcessing={isProcessing}
            onRecordingChange={onRecordingChange}
            onAudioReady={onAudioReady}
          />
          <span 
            className="bmw-caption px-3 py-1" 
            style={{ 
              border: '1px solid var(--color-hairline-strong)', 
              backgroundColor: 'var(--color-canvas)',
              color: 'var(--color-ink)'
            }}
          >
            {isRecording ? "Đang nghe..." : isProcessing ? "Đang xử lý..." : "Sẵn sàng"}
          </span>
          {currentTranscript ? (
            <span className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>Bạn đã nói: {currentTranscript}</span>
          ) : null}
        </div>

        <ChatMessageList messages={messages} isProcessing={isProcessing} />

        <form className="flex flex-col gap-4 md:flex-row" onSubmit={handleSubmit}>
          <input
            className="bmw-text-input flex-1"
            placeholder="Nhập lệnh, ví dụ: bật đèn, servo 90 độ..."
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <button type="submit" className="bmw-button-secondary" disabled={isProcessing}>
            Gửi
          </button>
        </form>

        {error ? (
          <div 
            className="p-4" 
            style={{ backgroundColor: 'var(--color-error)', color: 'var(--color-on-dark)' }}
          >
            {error}
          </div>
        ) : null}
        <AudioReplyPlayer audioUrl={activeAudioUrl} />
      </div>
    </div>
  );
}
