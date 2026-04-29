import { useEffect } from "react";
import DeviceControlPanel from "../components/controls/DeviceControlPanel";
import Navbar from "../components/layout/Navbar";
import StatusBanner from "../components/layout/StatusBanner";
import ActiveDevicesCard from "../components/overview/ActiveDevicesCard";
import OverviewCards from "../components/overview/OverviewCards";
import TelemetryChartCard from "../components/telemetry/TelemetryChartCard";
import VoiceChatPanel from "../components/voice/VoiceChatPanel";
import { useDashboardStore } from "../store/useDashboardStore";
import { useVoiceAssistantStore } from "../store/useVoiceAssistantStore";

export default function DashboardPage() {
  const {
    health,
    latest,
    deviceStatus,
    history,
    rangeHours,
    isLoading,
    error,
    loadDashboard,
    setRangeHours,
    updateLed,
    updateServo,
  } = useDashboardStore();

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

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-4 py-6 md:px-6">
      <Navbar />
      <StatusBanner health={health} error={error} />

      <OverviewCards latest={latest} deviceStatus={deviceStatus} />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
          <TelemetryChartCard
            history={history}
            rangeHours={rangeHours}
            onRangeChange={setRangeHours}
          />
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

        <div className="space-y-6">
          <ActiveDevicesCard deviceStatus={deviceStatus} />
          <DeviceControlPanel
            deviceStatus={deviceStatus}
            onToggleLed={updateLed}
            onCommitServo={updateServo}
            busy={isLoading || isProcessing}
          />
        </div>
      </div>
    </div>
  );
}
