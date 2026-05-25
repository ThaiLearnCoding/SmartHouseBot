import DeviceControlPanel from "../components/controls/DeviceControlPanel";
import { useDashboardStore } from "../store/useDashboardStore";
import { useVoiceAssistantStore } from "../store/useVoiceAssistantStore";

export default function ControlsPage() {
  const deviceStatus = useDashboardStore((state) => state.deviceStatus);
  const isLoading = useDashboardStore((state) => state.isLoading);
  const updateLed = useDashboardStore((state) => state.updateLed);
  const updateServo = useDashboardStore((state) => state.updateServo);
  const isProcessing = useVoiceAssistantStore((state) => state.isProcessing);

  return (
    <div className="flex flex-col">
      {/* Hero Photo Band (Simulated with canvas color for now) */}
      <div 
        className="w-full flex items-center justify-center text-center"
        style={{ 
          backgroundColor: 'var(--color-surface-soft)', 
          padding: '80px 24px',
          borderBottom: '1px solid var(--color-hairline)'
        }}
      >
        <div className="max-w-[1440px] mx-auto">
          <h1 className="bmw-display-lg" style={{ color: "var(--color-ink)" }}>ĐIỀU KHIỂN THIẾT BỊ</h1>
        </div>
      </div>

      <div className="mx-auto max-w-[1440px] w-full px-4 py-16 md:px-6">
        <div className="max-w-2xl mx-auto">
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
