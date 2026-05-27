import { formatHumidity, formatStatusSource, formatTemperature } from "../../lib/utils";

function OverviewCard({ title, value, subtitle }) {
  return (
    <div 
      className="flex flex-col p-6"
      style={{ 
        backgroundColor: 'var(--color-surface-card)', 
        border: '1px solid var(--color-hairline)'
      }}
    >
      <p className="bmw-body-sm mb-2" style={{ color: 'var(--color-muted)' }}>{title}</p>
      <h2 className="bmw-display-md mb-2" style={{ color: 'var(--color-ink)' }}>{value}</h2>
      <p className="bmw-caption" style={{ color: 'var(--color-muted)' }}>{subtitle}</p>
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
        subtitle={`Nguồn trạng thái: ${formatStatusSource(deviceStatus?.status_source)}`}
      />
    </div>
  );
}
