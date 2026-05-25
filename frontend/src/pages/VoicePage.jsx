import VoiceChatPanel from "../components/voice/VoiceChatPanel";
import { useVoiceAssistantStore } from "../store/useVoiceAssistantStore";

export default function VoicePage() {
  const {
    messages,
    isRecording,
    isProcessing,
    currentTranscript,
    activeAudioUrl,
    error: voiceError,
    setRecording,
    submitAudio,
    submitText,
  } = useVoiceAssistantStore();

  return (
    <div className="flex flex-col">
      {/* Hero Photo Band (Simulated) */}
      <div 
        className="w-full flex items-center justify-center text-center"
        style={{ 
          backgroundColor: 'var(--color-surface-soft)', 
          padding: '80px 24px',
          borderBottom: '1px solid var(--color-hairline)'
        }}
      >
        <div className="max-w-[1440px] mx-auto">
          <h1 className="bmw-display-lg" style={{ color: 'var(--color-ink)' }}>VOICE ASSISTANT</h1>
        </div>
      </div>

      <div className="mx-auto max-w-[1440px] w-full px-4 py-16 md:px-6">
        <div className="max-w-3xl mx-auto">
          <VoiceChatPanel
            messages={messages}
            isRecording={isRecording}
            isProcessing={isProcessing}
            currentTranscript={currentTranscript}
            activeAudioUrl={activeAudioUrl}
            error={voiceError}
            onRecordingChange={setRecording}
            onAudioReady={submitAudio}
            onSendText={submitText}
          />
        </div>
      </div>
    </div>
  );
}
