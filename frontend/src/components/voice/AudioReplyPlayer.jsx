import { useEffect, useRef } from "react";

export default function AudioReplyPlayer({ audioUrl }) {
  const audioRef = useRef(null);

  useEffect(() => {
    if (audioRef.current && audioUrl) {
      audioRef.current.play().catch(() => {});
    }
  }, [audioUrl]);

  if (!audioUrl) {
    return null;
  }

  return (
    <div>
      <p className="mb-2 text-sm font-medium">Phản hồi bằng giọng nói</p>
      <audio ref={audioRef} controls className="w-full" src={audioUrl} />
    </div>
  );
}
