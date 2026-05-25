export default function ActiveDevicesCard({ deviceStatus }) {
  return (
    <div className="bmw-card" style={{ border: '1px solid var(--color-hairline)' }}>
      <div className="bmw-card-header">
        <h2 className="bmw-card-title">Tổng quan thiết bị</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div 
          className="p-6"
          style={{ backgroundColor: 'var(--color-surface-soft)' }}
        >
          <p className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>LED</p>
          <p className="mt-2 bmw-display-sm" style={{ color: 'var(--color-ink)' }}>
            {deviceStatus?.led_on == null ? "Không rõ" : deviceStatus.led_on ? "Bật" : "Tắt"}
          </p>
        </div>
        <div 
          className="p-6"
          style={{ backgroundColor: 'var(--color-surface-soft)' }}
        >
          <p className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>Góc Servo</p>
          <p className="mt-2 bmw-display-sm" style={{ color: 'var(--color-ink)' }}>
            {deviceStatus?.servo_angle == null ? "Không rõ" : `${deviceStatus.servo_angle} độ`}
          </p>
        </div>
      </div>
    </div>
  );
}
