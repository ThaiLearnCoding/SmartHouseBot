const OPTIONS = [6, 12, 24, 48];

export default function TimeRangeSelector({ value, onChange }) {
  return (
    <div className="join">
      {OPTIONS.map((hours) => (
        <button
          key={hours}
          type="button"
          className={`join-item btn btn-sm ${value === hours ? "btn-primary" : "btn-outline"}`}
          onClick={() => onChange(hours)}
        >
          {hours}h
        </button>
      ))}
    </div>
  );
}
