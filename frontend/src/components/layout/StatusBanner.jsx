export default function StatusBanner({ health, error }) {
  if (error) {
    return <div className="alert alert-error shadow-sm">{error}</div>;
  }

  if (!health) {
    return <div className="alert alert-info shadow-sm">Connecting to backend services...</div>;
  }

  return (
    <div className="alert alert-success shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <span>Backend ready</span>
        <span className="badge badge-outline">Whisper: {health.whisper_available ? "ready" : "missing"}</span>
        <span className="badge badge-outline">TTS: {health.tts_available ? "ready" : "missing"}</span>
        <span className="badge badge-outline">LLM: {health.llm_enabled ? health.ollama_model : "disabled"}</span>
      </div>
    </div>
  );
}
