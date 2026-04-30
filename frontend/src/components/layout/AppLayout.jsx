import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import StatusBanner from "./StatusBanner";
import { useDashboardStore } from "../../store/useDashboardStore";
import { useVoiceAssistantStore } from "../../store/useVoiceAssistantStore";
import { useEffect } from "react";

export default function AppLayout() {
  const { health, error, loadDashboard, setError: setDashboardError } = useDashboardStore();
  const { setError: setVoiceError } = useVoiceAssistantStore();
  const location = useLocation();

  useEffect(() => {
    loadDashboard();
    
    // Set up polling for near real-time updates every 5 seconds
    const interval = setInterval(() => {
      useDashboardStore.getState().refreshDashboard();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [loadDashboard]);

  useEffect(() => {
    // Clear errors when navigating to a different page
    setDashboardError(null);
    setVoiceError(null);
  }, [location.pathname, setDashboardError, setVoiceError]);

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar />
      <StatusBanner health={health} error={error} />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
