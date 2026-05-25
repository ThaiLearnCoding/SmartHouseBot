import { useEffect, useState } from "react";

export default function ServoSlider({ angle, onCommit, disabled }) {
  const [localAngle, setLocalAngle] = useState(angle ?? 90);

  useEffect(() => {
    if (angle != null) {
      setLocalAngle(angle);
    }
  }, [angle]);

  return (
    <div 
      className="p-4 flex flex-col gap-4"
      style={{ backgroundColor: 'var(--color-surface-soft)' }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="bmw-title-sm">Góc Servo</p>
          <p className="bmw-body-sm" style={{ color: 'var(--color-muted)' }}>Kéo thanh trượt để gửi góc mới.</p>
        </div>
        <span className="bmw-caption px-3 py-1" style={{ border: '1px solid var(--color-hairline-strong)', backgroundColor: 'var(--color-canvas)' }}>{localAngle} độ</span>
      </div>

      <input
        type="range"
        min="0"
        max="180"
        value={localAngle}
        disabled={disabled}
        className="w-full h-2 appearance-none cursor-pointer"
        style={{ 
          backgroundColor: 'var(--color-hairline-strong)',
          accentColor: 'var(--color-primary)'
        }}
        onChange={(event) => setLocalAngle(Number(event.target.value))}
        onMouseUp={() => onCommit(localAngle)}
        onTouchEnd={() => onCommit(localAngle)}
      />
    </div>
  );
}
