import { useEffect, useRef, useState } from "react";

function decodeBase64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

export default function StreamingAudioPlayer({ audioChunks, onChunkPlayed }) {
    const audioContextRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);

    useEffect(() => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }
    }, []);

    useEffect(() => {
        if (isPlaying || audioChunks.length === 0) return;
        const audioContext = audioContextRef.current;
        if (!audioContext) return;

        const nextChunk = audioChunks[0];
        setIsPlaying(true);

        audioContext.decodeAudioData(decodeBase64ToArrayBuffer(nextChunk))
            .then((buffer) => {
                const source = audioContext.createBufferSource();
                source.buffer = buffer;
                source.connect(audioContext.destination);
                source.start();
                source.onended = () => {
                    setIsPlaying(false);
                    onChunkPlayed();
                };
            })
            .catch(() => {
                setIsPlaying(false);
                onChunkPlayed();
            });
    }, [audioChunks, isPlaying, onChunkPlayed]);

    if (audioChunks.length === 0) {
        return null;
    }

    return (
        <div>
            <p className="mb-2 text-sm font-medium">Phản hồi bằng giọng nói (đang phát)</p>
        </div>
    );
}
