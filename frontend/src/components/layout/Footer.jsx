import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer style={{ backgroundColor: "var(--color-surface-soft)", padding: "24px", marginTop: "auto" }}>
      <div className="mx-auto max-w-[1440px] flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="bmw-caption text-[var(--color-muted)]">
          &copy; 2026 SmartHouseBot. Bảo lưu mọi quyền.
        </p>
        <div className="flex gap-4">
          <span className="bmw-caption text-[var(--color-muted)]">Chính sách bảo mật</span>
          <span className="bmw-caption text-[var(--color-muted)]">Điều khoản sử dụng</span>
        </div>
      </div>
    </footer>
  );
}
