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
    <div className="card bg-base-100 shadow-sm">
      <div className="card-body gap-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="card-title">Telemetry Trends</h2>
            <p className="text-sm text-base-content/60">
              Lịch sử nhiệt độ và độ ẩm trong khoảng thời gian đã chọn.
            </p>
          </div>
          <TimeRangeSelector value={rangeHours} onChange={onRangeChange} />
        </div>

        <div className="h-80">
          {chartData.length === 0 ? (
            <div className="flex h-full items-center justify-center rounded-box border border-dashed border-base-300 bg-base-200 text-sm text-base-content/60">
              Không tìm thấy dữ liệu CoreIoT trong khoảng thời gian này.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" minTickGap={28} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="temperature"
                  stroke="#ef4444"
                  dot={chartData.length <= 12}
                  strokeWidth={2}
                  name="Nhiệt độ"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="humidity"
                  stroke="#3b82f6"
                  dot={chartData.length <= 12}
                  strokeWidth={2}
                  name="Độ ẩm"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
