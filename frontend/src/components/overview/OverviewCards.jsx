import { formatHumidity, formatTemperature } from "../../lib/utils";

function OverviewCard({ title, value, subtitle }) {
  return (
    <div className="card bg-base-100 shadow-sm">
      <div className="card-body">
        <p className="text-sm text-base-content/60">{title}</p>
        <h2 className="text-3xl font-semibold">{value}</h2>
        <p className="text-sm text-base-content/60">{subtitle}</p>
      </div>
    </div>
  );
}

export default function OverviewCards({ latest, deviceStatus }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <OverviewCard
        title="Nhiệt độ"
        value={formatTemperature(latest?.temperature)}
        subtitle="Đọc thời gian thực"
      />
      <OverviewCard
        title="Độ ẩm"
        value={formatHumidity(latest?.humidity)}
        subtitle="Dữ liệu CoreIoT mới nhất"
      />
      <OverviewCard
        title="Thiết bị hoạt động"
        value={deviceStatus?.active_devices ?? 0}
        subtitle={`Nguồn trạng thái: ${deviceStatus?.status_source ?? "không rõ"}`}
      />
    </div>
  );
}
