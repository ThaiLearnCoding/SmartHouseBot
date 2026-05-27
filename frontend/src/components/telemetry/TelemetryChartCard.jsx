import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatChartTimestamp, formatChartTooltipTime, formatSensorValue } from "../../lib/utils";
import TimeRangeSelector from "./TimeRangeSelector";

const tooltipStyle = {
  backgroundColor: "var(--color-canvas)",
  border: "1px solid var(--color-hairline-strong)",
  borderRadius: "0px",
};

const legendStyle = { fontSize: "14px", paddingTop: "16px" };

function normalizeTimestampMs(value) {
  if (value == null || Number.isNaN(Number(value))) return null;
  const ts = Number(value);
  return ts < 1e12 ? ts * 1000 : ts;
}

export default function TelemetryChartCard({
  history,
  rangeHours,
  onRangeChange,
  isLoading,
}) {
  const chartData = useMemo(
    () =>
      history
        .map((point) => ({
          ...point,
          timestamp: normalizeTimestampMs(point.timestamp),
        }))
        .filter((point) => point.timestamp != null)
        .slice()
        .sort((a, b) => a.timestamp - b.timestamp),
    [history],
  );

  const hasData = useMemo(
    () =>
      chartData.some(
        (point) => point.temperature != null || point.humidity != null,
      ),
    [chartData],
  );

  const xDomain = useMemo(() => {
    const end = Date.now();
    const start = end - rangeHours * 3600 * 1000;
    return [start, end];
  }, [rangeHours]);

  return (
    <div className="bmw-card" style={{ border: "1px solid var(--color-hairline)" }}>
      <div className="bmw-card-header flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="bmw-card-title">Biểu đồ nhiệt độ & độ ẩm</h2>
          <p className="bmw-body-sm" style={{ color: "var(--color-muted)" }}>
            Lịch sử trong {rangeHours} giờ gần nhất.
          </p>
        </div>
        <TimeRangeSelector value={rangeHours} onChange={onRangeChange} />
      </div>

      <div className="h-80 w-full mt-8">
        {isLoading ? (
          <div
            className="flex h-full items-center justify-center text-sm"
            style={{
              border: "1px dashed var(--color-hairline-strong)",
              backgroundColor: "var(--color-surface-soft)",
              color: "var(--color-muted)",
            }}
          >
            Đang tải dữ liệu biểu đồ...
          </div>
        ) : !hasData ? (
          <div
            className="flex h-full items-center justify-center text-sm"
            style={{
              border: "1px dashed var(--color-hairline-strong)",
              backgroundColor: "var(--color-surface-soft)",
              color: "var(--color-muted)",
            }}
          >
            Không có dữ liệu trong khoảng thời gian này.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart key={rangeHours} data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-hairline-strong)" />
              <XAxis
                dataKey="timestamp"
                type="number"
                domain={xDomain}
                allowDataOverflow
                tickFormatter={(value) => formatChartTimestamp(value, rangeHours)}
                minTickGap={28}
                stroke="var(--color-muted)"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                yAxisId="left"
                stroke="var(--color-muted)"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatSensorValue(value)}
                unit="°C"
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="var(--color-muted)"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatSensorValue(value)}
                unit="%"
              />
              <Tooltip
                contentStyle={tooltipStyle}
                labelFormatter={(value) => formatChartTooltipTime(value)}
                formatter={(value, name) => [formatSensorValue(value), name]}
              />
              <Legend wrapperStyle={legendStyle} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="temperature"
                stroke="#1c69d4"
                dot={chartData.length <= 24}
                strokeWidth={2}
                name="Nhiệt độ (°C)"
                connectNulls
                isAnimationActive={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="humidity"
                stroke="#262626"
                dot={chartData.length <= 24}
                strokeWidth={2}
                name="Độ ẩm (%)"
                connectNulls
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
