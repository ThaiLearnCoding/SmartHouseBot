import { create } from "zustand";
import {
  fetchHealth,
  fetchLatestTelemetry,
  fetchTelemetryHistory,
  setLedState,
  setServoAngle,
} from "../services/dashboardApi";
import { getApiErrorMessage } from "../lib/axios";
import {
  applyHistoryResponse,
  getHistoryBuffer,
  readCachedHistory,
  resetHistoryBuffers,
} from "../lib/historyBuffer";

let dashboardErrorTimeout = null;
let refreshInFlight = false;

function deviceStatusFromLatest(latest, fallback = null) {
  return latest?.device_status ?? fallback;
}

export { resetHistoryBuffers };

export const useDashboardStore = create((set, get) => ({
  health: null,
  latest: null,
  deviceStatus: null,
  history: [],
  historySampleIntervalSeconds: 20,
  rangeHours: 24,
  isLoading: false,
  error: null,

  setError: (errorMsg) => {
    if (dashboardErrorTimeout) clearTimeout(dashboardErrorTimeout);
    set({ error: errorMsg });
    if (errorMsg) {
      dashboardErrorTimeout = setTimeout(() => {
        set({ error: null });
      }, 5000);
    }
  },

  refreshHealth: async () => {
    try {
      const health = await fetchHealth();
      set({ health });
    } catch (error) {
      console.warn("Health refresh failed:", error);
    }
  },

  refreshLatest: async () => {
    try {
      const latest = await fetchLatestTelemetry();
      const rangeHours = get().rangeHours;
      const buffer = getHistoryBuffer(rangeHours);
      const history = buffer.toArray().length > 0 ? buffer.patchLatest(latest) : get().history;

      set((state) => ({
        latest,
        history,
        deviceStatus: state.isLoading
          ? state.deviceStatus
          : deviceStatusFromLatest(latest, state.deviceStatus),
      }));
    } catch (error) {
      console.warn("Latest telemetry refresh failed:", error);
    }
  },

  refreshHistory: async ({ force = false } = {}) => {
    const rangeHours = get().rangeHours;

    if (!force) {
      const cached = readCachedHistory(rangeHours);
      if (cached) {
        set(cached);
        return;
      }
    }

    try {
      const response = await fetchTelemetryHistory(rangeHours);
      set(applyHistoryResponse(response, rangeHours));
    } catch (error) {
      console.warn("Chart history refresh failed:", error);
    }
  },

  ensureHistory: async () => {
    const rangeHours = get().rangeHours;
    const cached = readCachedHistory(rangeHours);
    if (cached) {
      set(cached);
      return;
    }

    set({ isLoading: true });
    try {
      await get().refreshHistory({ force: true });
    } finally {
      set({ isLoading: false });
    }
  },

  loadDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const rangeHours = get().rangeHours;
      const [health, latest, historyResponse] = await Promise.all([
        fetchHealth(),
        fetchLatestTelemetry(),
        fetchTelemetryHistory(rangeHours),
      ]);

      set({
        health,
        latest,
        ...applyHistoryResponse(historyResponse, rangeHours),
        deviceStatus: deviceStatusFromLatest(latest),
        isLoading: false,
      });
    } catch (error) {
      get().setError(getApiErrorMessage(error, "Không tải được bảng điều khiển."));
      set({ isLoading: false });
    }
  },

  refreshDashboard: async ({ includeHistory = true, includeHealth = true } = {}) => {
    if (refreshInFlight) {
      return;
    }

    refreshInFlight = true;
    try {
      const tasks = [get().refreshLatest()];
      if (includeHealth) {
        tasks.push(get().refreshHealth());
      }
      if (includeHistory) {
        tasks.push(get().refreshHistory());
      }
      await Promise.all(tasks);
    } finally {
      refreshInFlight = false;
    }
  },

  setRangeHours: async (rangeHours) => {
    const cached = readCachedHistory(rangeHours);
    if (cached) {
      set({ rangeHours, ...cached, isLoading: false, error: null });
      return;
    }

    set({ rangeHours, isLoading: true, error: null });
    try {
      const response = await fetchTelemetryHistory(rangeHours);
      set({ ...applyHistoryResponse(response, rangeHours), isLoading: false });
    } catch (error) {
      get().setError(getApiErrorMessage(error, "Không tải được dữ liệu biểu đồ."));
      set({ isLoading: false });
    }
  },

  updateLed: async (on) => {
    const prevStatus = get().deviceStatus;

    set({
      deviceStatus: {
        ...prevStatus,
        led_on: on,
      },
      isLoading: true,
    });

    try {
      const result = await setLedState(on);
      set({ deviceStatus: result.status, isLoading: false });
      return result;
    } catch (error) {
      set({ deviceStatus: prevStatus, isLoading: false });
      get().setError(getApiErrorMessage(error, "Không cập nhật được đèn LED."));
      return null;
    }
  },

  updateServo: async (angle) => {
    const prevStatus = get().deviceStatus;

    set({
      deviceStatus: {
        ...prevStatus,
        servo_angle: angle,
      },
      isLoading: true,
    });

    try {
      const result = await setServoAngle(angle);
      set({ deviceStatus: result.status, isLoading: false });
      return result;
    } catch (error) {
      set({ deviceStatus: prevStatus, isLoading: false });
      get().setError(getApiErrorMessage(error, "Không cập nhật được servo."));
      return null;
    }
  },
}));
