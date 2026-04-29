export default function LedToggle({ ledOn, onToggle, disabled }) {
  return (
    <label 
      className="flex items-center justify-between p-4"
      style={{ backgroundColor: 'var(--color-surface-soft)' }}
    >
      <div>
        <p className="bmw-title-sm">Điều khiển đèn LED</p>
        <p className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>Bật/tắt đèn LED không cần dùng giọng nói.</p>
      </div>
      <input
        type="checkbox"
        className="w-12 h-6 cursor-pointer appearance-none bg-[var(--color-hairline-strong)] checked:bg-[var(--color-primary)] rounded-full relative transition-colors duration-200 focus:outline-none after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all after:duration-200 checked:after:translate-x-6"
        style={{
          border: 'none',
          outline: 'none',
        }}
        checked={Boolean(ledOn)}
        disabled={disabled}
        onChange={(event) => onToggle(event.target.checked)}
      />
    </label>
  );
}
