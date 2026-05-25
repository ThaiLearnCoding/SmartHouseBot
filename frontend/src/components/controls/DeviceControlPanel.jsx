import LedToggle from "./LedToggle";
import ServoSlider from "./ServoSlider";

export default function DeviceControlPanel({ deviceStatus, onToggleLed, onCommitServo, busy }) {
  return (
    <div className="bmw-card" style={{ border: '1px solid var(--color-hairline)' }}>
      <div className="bmw-card-header">
        <div className="flex items-center justify-between">
          <h2 className="bmw-card-title">Trung tâm điều khiển</h2>
          {busy && (
            <span className="bmw-caption flex items-center gap-2" style={{ color: 'var(--color-primary)' }}>
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: 'var(--color-primary)' }}></span>
              Đang xử lý...
            </span>
          )}
        </div>
        <p className="bmw-body-sm mt-2" style={{ color: 'var(--color-muted)' }}>
          Điều khiển thủ công cho lệnh đèn LED và servo.
        </p>
      </div>
      <div className="flex flex-col gap-6">
        <LedToggle ledOn={deviceStatus?.led_on} onToggle={onToggleLed} disabled={busy} />
        <ServoSlider angle={deviceStatus?.servo_angle} onCommit={onCommitServo} disabled={busy} />
      </div>
    </div>
  );
}
