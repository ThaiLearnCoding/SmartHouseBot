export default function ActiveDevicesCard({ deviceStatus }) {
  return (
    <div className="card bg-base-100 shadow-sm">
      <div className="card-body">
        <h2 className="card-title">Device Overview</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-box bg-base-200 p-4">
            <p className="text-sm text-base-content/60">LED</p>
            <p className="mt-2 text-xl font-semibold">
              {deviceStatus?.led_on == null ? "Không rõ" : deviceStatus.led_on ? "Bật" : "Tắt"}
            </p>
          </div>
          <div className="rounded-box bg-base-200 p-4">
            <p className="text-sm text-base-content/60">Góc Servo</p>
            <p className="mt-2 text-xl font-semibold">
              {deviceStatus?.servo_angle == null ? "Không rõ" : `${deviceStatus.servo_angle} độ`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
