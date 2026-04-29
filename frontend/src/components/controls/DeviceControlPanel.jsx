import LedToggle from "./LedToggle";
import ServoSlider from "./ServoSlider";

export default function DeviceControlPanel({ deviceStatus, onToggleLed, onCommitServo, busy }) {
  return (
    <div className="card bg-base-100 shadow-sm">
      <div className="card-body gap-4">
        <div>
          <h2 className="card-title">Device Control Center</h2>
          <p className="text-sm text-base-content/60">
            Điều khiển thủ công cho lệnh đèn LED và servo.
          </p>
        </div>
        <LedToggle ledOn={deviceStatus?.led_on} onToggle={onToggleLed} disabled={busy} />
        <ServoSlider angle={deviceStatus?.servo_angle} onCommit={onCommitServo} disabled={busy} />
      </div>
    </div>
  );
}
