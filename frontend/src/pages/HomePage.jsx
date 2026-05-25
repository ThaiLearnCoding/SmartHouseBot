import { Link } from "react-router-dom";
import ActiveDevicesCard from "../components/overview/ActiveDevicesCard";
import OverviewCards from "../components/overview/OverviewCards";
import { useDashboardStore } from "../store/useDashboardStore";

export default function HomePage() {
  const { latest, deviceStatus } = useDashboardStore();

  return (
    <div className="flex flex-col">
      {/* Hero Band Dark */}
      <div 
        className="flex flex-col items-center text-center w-full"
        style={{ 
          backgroundColor: 'var(--color-surface-dark)', 
          color: 'var(--color-on-dark)', 
          padding: '80px 24px' 
        }}
      >
        <div className="max-w-[1440px] w-full mx-auto">
          <h1 className="bmw-display-xl mb-4">YOUR HOME ECOSYSTEM</h1>
          <p className="bmw-display-sm mb-8" style={{ color: 'var(--color-on-dark-soft)' }}>
            Dễ dàng quản lý và điều khiển các thiết bị trong ngôi nhà của bạn
          </p>
          <div className="flex gap-4 justify-center">
            <Link 
              to="/controls" 
              className="bmw-button-primary"
            >
              DEVICE CONTROLS
            </Link>
            <Link 
              to="/voice" 
              className="bmw-button-secondary !bg-transparent !text-white !border-white hover:!bg-white/20" 
            >
              VOICE ASSISTANT
            </Link>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1440px] w-full px-4 py-16 md:px-6 space-y-12">
        <section>
          <h2 className="bmw-display-lg mb-8" style={{ color: 'var(--color-ink)' }}>SYSTEM OVERVIEW</h2>
          <OverviewCards latest={latest} deviceStatus={deviceStatus} />
        </section>

        <section>
          <h2 className="bmw-display-md mb-8" style={{ color: 'var(--color-ink)' }}>ACTIVE DEVICES</h2>
          <ActiveDevicesCard deviceStatus={deviceStatus} />
        </section>
      </div>
    </div>
  );
}
