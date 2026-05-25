import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer style={{ backgroundColor: 'var(--color-surface-soft)', padding: '24px', marginTop: 'auto' }}>
      <div className="mx-auto max-w-[1440px] flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="bmw-caption text-[var(--color-muted)]">&copy; 2026 SmartHouseBot. All rights reserved.</p>
        <div className="flex gap-4">
          <span className="bmw-caption text-[var(--color-muted)]">Privacy Policy</span>
          <span className="bmw-caption text-[var(--color-muted)]">Terms of Service</span>
        </div>
      </div>
    </footer>
  );
}
