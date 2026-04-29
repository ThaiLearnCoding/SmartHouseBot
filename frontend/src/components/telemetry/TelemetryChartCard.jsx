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
import { formatTimestamp } from "../../lib/utils";
import TimeRangeSelector from "./TimeRangeSelector";

export default function TelemetryChartCard({ history, rangeHours, onRangeChange }) {
  const chartData = history.map((point) => ({
    ...point,
    label: formatTimestamp(point.iso_time),
  }));

  return (
    <div className="bmw-card" style={{ border: '1px solid var(--color-hairline)' }}>
      <div className="bmw-card-header flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="bmw-card-title">Telemetry Trends</h2>
          <p className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>
            Lịch sử nhiệt độ và độ ẩm trong khoảng thời gian đã chọn.
          </p>
        </div>
        <TimeRangeSelector value={rangeHours} onChange={onRangeChange} />
      </div>

      <div className="h-80 w-full mt-8">
        {chartData.length === 0 ? (
          <div 
            className="flex h-full items-center justify-center text-sm"
            style={{ 
              border: '1px dashed var(--color-hairline-strong)', 
              backgroundColor: 'var(--color-surface-soft)',
              color: 'var(--color-muted)'
            }}
          >
            Không tìm thấy dữ liệu CoreIoT trong khoảng thời gian này.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-hairline-strong)" />
              <XAxis dataKey="label" minTickGap={28} stroke="var(--color-muted)" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="left" stroke="var(--color-muted)" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" stroke="var(--color-muted)" tick={{ fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'var(--color-canvas)', 
                  border: '1px solid var(--color-hairline-strong)',
                  borderRadius: '0px'
                }} 
              />
              <Legend wrapperStyle={{ fontSize: '14px', paddingTop: '16px' }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="temperature"
                stroke="#1c69d4"
                dot={chartData.length <= 12}
                strokeWidth={2}
                name="Nhiệt độ"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="humidity"
                stroke="#262626"
                dot={chartData.length <= 12}
                strokeWidth={2}
                name="Độ ẩm"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
