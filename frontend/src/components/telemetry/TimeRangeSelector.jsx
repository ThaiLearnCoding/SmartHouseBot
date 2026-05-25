const OPTIONS = [6, 12, 24, 48];

export default function TimeRangeSelector({ value, onChange }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {OPTIONS.map((hours) => {
        const isActive = value === hours;
        return (
          <button
            key={hours}
            type="button"
            className="bmw-caption px-3 py-2 cursor-pointer transition-colors"
            style={{
              backgroundColor: isActive ? 'var(--color-ink)' : 'var(--color-canvas)',
              color: isActive ? 'var(--color-on-dark)' : 'var(--color-ink)',
              border: isActive ? '1px solid var(--color-ink)' : '1px solid var(--color-hairline-strong)',
              borderRadius: '0px'
            }}
            onClick={() => onChange(hours)}
          >
            {hours} giờ
          </button>
        );
      })}
    </div>
  );
}
