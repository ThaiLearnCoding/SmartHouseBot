import { useEffect, useState } from "react";

export default function ServoSlider({ angle, onCommit, disabled }) {
  const [localAngle, setLocalAngle] = useState(angle ?? 90);

  useEffect(() => {
    if (angle != null) {
      setLocalAngle(angle);
    }
  }, [angle]);

  return (
    <div className="rounded-box bg-base-200 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="font-medium">Góc Servo</p>
          <p className="text-sm text-base-content/60">Kéo thanh trượt để gửi góc mới.</p>
        </div>
        <span className="badge badge-outline">{localAngle} độ</span>
      </div>

      <input
        type="range"
        min="0"
        max="180"
        value={localAngle}
        disabled={disabled}
        className="range range-primary"
        onChange={(event) => setLocalAngle(Number(event.target.value))}
        onMouseUp={() => onCommit(localAngle)}
        onTouchEnd={() => onCommit(localAngle)}
      />
    </div>
  );
}
