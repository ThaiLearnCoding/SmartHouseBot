import { useEffect, useRef } from "react";

export default function ChatMessageList({ messages, isProcessing }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, isProcessing]);

  return (
    <div
      ref={containerRef}
      className="flex max-h-96 flex-col gap-3 overflow-y-auto rounded-box bg-base-200 p-4"
    >
      {messages.length === 0 ? (
        <p className="text-sm text-base-content/60">
          Hãy nói hoặc nhập một lệnh như: bật đèn, tắt đèn, servo 90 độ, đọc nhiệt độ độ ẩm, tình trạng nhà hôm nay.
        </p>
      ) : null}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`chat ${message.role === "assistant" ? "chat-start" : "chat-end"}`}
        >
          <div className="chat-bubble">
            <p>{message.text}</p>
            {message.intent ? (
              <p className="mt-2 text-xs opacity-70">Message: {message.intent}</p>
            ) : null}
          </div>
        </div>
      ))}

      {isProcessing ? (
        <div className="chat chat-start">
          <div className="chat-bubble">
            <span className="loading loading-dots loading-md" />
          </div>
        </div>
      ) : null}
    </div>
  );
}
