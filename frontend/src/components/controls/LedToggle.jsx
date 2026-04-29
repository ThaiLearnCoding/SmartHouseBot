export default function LedToggle({ ledOn, onToggle, disabled }) {
  return (
    <label className="flex items-center justify-between rounded-box bg-base-200 p-4">
      <div>
        <p className="font-medium">Điều khiển đèn LED</p>
        <p className="text-sm text-base-content/60">Bật/tắt đèn LED không cần dùng giọng nói.</p>
      </div>
      <input
        type="checkbox"
        className="toggle toggle-primary"
        checked={Boolean(ledOn)}
        disabled={disabled}
        onChange={(event) => onToggle(event.target.checked)}
      />
    </label>
  );
}
