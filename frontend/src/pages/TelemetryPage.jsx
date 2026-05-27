import { useEffect } from "react";
import TelemetryChartCard from "../components/telemetry/TelemetryChartCard";
import { useDashboardStore } from "../store/useDashboardStore";

export default function TelemetryPage() {
  const history = useDashboardStore((state) => state.history);
  const rangeHours = useDashboardStore((state) => state.rangeHours);
  const isLoading = useDashboardStore((state) => state.isLoading);
  const setRangeHours = useDashboardStore((state) => state.setRangeHours);
  const ensureHistory = useDashboardStore((state) => state.ensureHistory);

  useEffect(() => {
    ensureHistory();
  }, [ensureHistory, rangeHours]);

  return (
    <div className="flex flex-col">
      <div
        className="w-full flex items-center justify-center text-center"
        style={{
          backgroundColor: "var(--color-canvas)",
          padding: "80px 24px",
          borderBottom: "1px solid var(--color-hairline)",
        }}
      >
        <div className="max-w-[1440px] mx-auto">
          <h1 className="bmw-display-lg" style={{ color: "var(--color-ink)" }}>
            BIỂU ĐỒ & LỊCH SỬ
          </h1>
        </div>
      </div>

      <div className="mx-auto max-w-[1440px] w-full px-4 py-16 md:px-6">
        <div className="max-w-4xl mx-auto">
          <TelemetryChartCard
            history={history}
            rangeHours={rangeHours}
            onRangeChange={setRangeHours}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}
