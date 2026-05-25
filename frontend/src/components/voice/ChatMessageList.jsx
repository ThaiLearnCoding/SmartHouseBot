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
      className="flex max-h-96 flex-col gap-4 overflow-y-auto p-4"
      style={{ backgroundColor: 'var(--color-surface-soft)', border: '1px solid var(--color-hairline)' }}
    >
      {messages.length === 0 ? (
        <p className="bmw-body-sm text-center" style={{ color: 'var(--color-muted)' }}>
          Hãy nói hoặc nhập một lệnh như: bật đèn, tắt đèn, servo 90 độ, đọc nhiệt độ độ ẩm, tình trạng nhà hôm nay.
        </p>
      ) : null}

      {messages.map((message) => {
        const isAssistant = message.role === "assistant";
        return (
          <div
            key={message.id}
            className={`flex w-full ${isAssistant ? "justify-start" : "justify-end"}`}
          >
            <div 
              className="max-w-[80%] p-4"
              style={{ 
                backgroundColor: isAssistant ? 'var(--color-canvas)' : 'var(--color-ink)',
                color: isAssistant ? 'var(--color-ink)' : 'var(--color-on-dark)',
                border: isAssistant ? '1px solid var(--color-hairline-strong)' : 'none',
              }}
            >
              <p className="bmw-body-md">{message.text}</p>
              {message.intent ? (
                <p className="mt-2 bmw-caption" style={{ color: isAssistant ? 'var(--color-muted)' : 'var(--color-on-dark-soft)' }}>
                  Intent: {message.intent}
                </p>
              ) : null}
            </div>
          </div>
        );
      })}

      {isProcessing ? (
        <div className="flex w-full justify-start">
          <div 
            className="p-4 flex items-center gap-2"
            style={{ 
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline-strong)',
            }}
          >
            <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: 'var(--color-muted)' }}></span>
            <span className="w-2 h-2 rounded-full animate-pulse delay-100" style={{ backgroundColor: 'var(--color-muted)' }}></span>
            <span className="w-2 h-2 rounded-full animate-pulse delay-200" style={{ backgroundColor: 'var(--color-muted)' }}></span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
