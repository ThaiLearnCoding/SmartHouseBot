export default function Navbar() {
  return (
    <div className="navbar rounded-box bg-base-100/90 px-6 shadow-sm backdrop-blur">
      <div className="flex-1">
        <div>
          <p className="text-sm text-base-content/60">SmartHouseBot</p>
          <h1 className="text-2xl font-semibold text-base-content">Smart Home Dashboard</h1>
        </div>
      </div>
      <div className="badge badge-primary badge-outline">Local AI + CoreIoT</div>
    </div>
  );
}
