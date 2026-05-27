import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const location = useLocation();

  const getLinkStyle = (path) => {
    const isActive = location.pathname === path;
    return {
      fontFamily: "var(--font-family)",
      fontSize: "14px",
      fontWeight: isActive ? 700 : 400,
      letterSpacing: "0.3px",
      color: isActive ? "var(--color-primary)" : "var(--color-ink)",
      borderBottom: isActive ? "2px solid var(--color-primary)" : "2px solid transparent",
      height: "100%",
      display: "flex",
      alignItems: "center",
      transition: "all 0.2s ease-in-out",
    };
  };

  return (
    <div
      className="sticky top-0 z-50 flex items-center justify-between w-full"
      style={{
        backgroundColor: "var(--color-canvas)",
        color: "var(--color-ink)",
        height: "64px",
        padding: "0 24px",
        borderBottom: "1px solid var(--color-hairline)",
      }}
    >
      <div className="flex items-center gap-8 h-full">
        <Link to="/" className="bmw-title-md flex items-center gap-2">
          <span>SmartHouseBot</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 h-full">
          <Link to="/" style={getLinkStyle("/")}>Tổng quan</Link>
          <Link to="/controls" style={getLinkStyle("/controls")}>Điều khiển</Link>
          <Link to="/telemetry" style={getLinkStyle("/telemetry")}>Biểu đồ</Link>
          <Link to="/voice" style={getLinkStyle("/voice")}>Trợ lý giọng nói</Link>
          <Link to="/logs" style={getLinkStyle("/logs")}>Nhật ký</Link>
        </nav>
      </div>
      <div className="flex items-center gap-4">
        <span className="bmw-caption" style={{ color: "var(--color-muted)" }}>
          AI cục bộ + CoreIoT
        </span>
      </div>
    </div>
  );
}
