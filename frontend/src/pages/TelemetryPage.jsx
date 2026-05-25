import TelemetryChartCard from "../components/telemetry/TelemetryChartCard";
import { useDashboardStore } from "../store/useDashboardStore";

export default function TelemetryPage() {
  const { history, rangeHours, setRangeHours } = useDashboardStore();

  return (
    <div className="flex flex-col">
      {/* Hero Photo Band (Simulated) */}
      <div 
        className="w-full flex items-center justify-center text-center"
        style={{ 
          backgroundColor: 'var(--color-canvas)', 
          padding: '80px 24px',
          borderBottom: '1px solid var(--color-hairline)'
        }}
      >
        <div className="max-w-[1440px] mx-auto">
          <h1 className="bmw-display-lg" style={{ color: 'var(--color-ink)' }}>TELEMETRY & HISTORY</h1>
        </div>
      </div>

      <div className="mx-auto max-w-[1440px] w-full px-4 py-16 md:px-6">
        <div className="max-w-4xl mx-auto">
          <TelemetryChartCard
            history={history}
            rangeHours={rangeHours}
            onRangeChange={setRangeHours}
          />
        </div>
      </div>
    </div>
  );
}
