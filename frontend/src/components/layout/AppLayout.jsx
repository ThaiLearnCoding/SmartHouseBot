import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import StatusBanner from "./StatusBanner";
import { useDashboardStore } from "../../store/useDashboardStore";
import { useVoiceAssistantStore } from "../../store/useVoiceAssistantStore";
import { useEffect } from "react";

const POLL_LATEST_MS = 5000;
const POLL_HISTORY_MS = 30000;
const POLL_HEALTH_MS = 60000;
const POLL_VOICE_LATEST_MS = 10000;

function getPollConfig(pathname) {
  if (pathname.startsWith("/telemetry")) {
    return {
      latestMs: POLL_LATEST_MS,
      historyMs: POLL_HISTORY_MS,
      healthMs: POLL_HEALTH_MS,
      includeHistory: true,
      includeHealth: true,
    };
  }

  if (pathname.startsWith("/voice")) {
    return {
      latestMs: POLL_VOICE_LATEST_MS,
      historyMs: null,
      healthMs: null,
      includeHistory: false,
      includeHealth: false,
    };
  }

  return {
    latestMs: POLL_LATEST_MS,
    historyMs: null,
    healthMs: POLL_HEALTH_MS,
    includeHistory: false,
    includeHealth: true,
  };
}

export default function AppLayout() {
  const health = useDashboardStore((state) => state.health);
  const error = useDashboardStore((state) => state.error);
  const loadDashboard = useDashboardStore((state) => state.loadDashboard);
  const refreshDashboard = useDashboardStore((state) => state.refreshDashboard);
  const setDashboardError = useDashboardStore((state) => state.setError);
  const setVoiceError = useVoiceAssistantStore((state) => state.setError);
  const location = useLocation();

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (location.pathname.startsWith("/telemetry")) {
      useDashboardStore.getState().ensureHistory();
    }

    const config = getPollConfig(location.pathname);
    const timers = [];

    timers.push(
      setInterval(() => {
        refreshDashboard({
          includeHistory: config.includeHistory,
          includeHealth: false,
        });
      }, config.latestMs),
    );

    if (config.historyMs) {
      timers.push(
        setInterval(() => {
          refreshDashboard({
            includeHistory: true,
            includeHealth: false,
          });
        }, config.historyMs),
      );
    }

    if (config.healthMs) {
      timers.push(
        setInterval(() => {
          refreshDashboard({
            includeHistory: false,
            includeHealth: true,
          });
        }, config.healthMs),
      );
    }

    return () => {
      timers.forEach((timer) => clearInterval(timer));
    };
  }, [location.pathname, refreshDashboard]);

  useEffect(() => {
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
