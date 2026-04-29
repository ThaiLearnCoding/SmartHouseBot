import { create } from "zustand";
import {
  fetchDeviceStatus,
  fetchHealth,
  fetchLatestTelemetry,
  fetchTelemetryHistory,
  setLedState,
  setServoAngle,
} from "../services/dashboardApi";
import { getApiErrorMessage } from "../lib/axios";

let dashboardErrorTimeout = null;

export const useDashboardStore = create((set, get) => ({
  health: null,
  latest: null,
  deviceStatus: null,
  history: [],
  rangeHours: 24,
  isLoading: false,
  error: null,

  setError: (errorMsg) => {
    if (dashboardErrorTimeout) clearTimeout(dashboardErrorTimeout);
    set({ error: errorMsg });
    if (errorMsg) {
      dashboardErrorTimeout = setTimeout(() => {
        set({ error: null });
      }, 10000);
    }
  },

  loadDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const [health, latest, history, deviceStatus] = await Promise.all([
        fetchHealth(),
        fetchLatestTelemetry(),
        fetchTelemetryHistory(get().rangeHours),
        fetchDeviceStatus(),
      ]);

      set({
        health,
        latest,
        history: history.points ?? [],
        deviceStatus: deviceStatus ?? latest?.device_status ?? null,
        isLoading: false,
      });
    } catch (error) {
      get().setError(getApiErrorMessage(error, "Failed to load dashboard."));
      set({ isLoading: false });
    }
  },

  setRangeHours: async (rangeHours) => {
    set({ rangeHours, isLoading: true, error: null });
    try {
      const history = await fetchTelemetryHistory(rangeHours);
      set({ history: history.points ?? [], isLoading: false });
    } catch (error) {
      get().setError(getApiErrorMessage(error, "Failed to load telemetry history."));
      set({ isLoading: false });
    }
  },

  updateLed: async (on) => {
    const prevStatus = get().deviceStatus;
    
    // Optimistic UI update
    set({
      deviceStatus: {
        ...prevStatus,
        led_on: on,
      },
      isLoading: true
    });

    try {
      const result = await setLedState(on);
      set({ deviceStatus: result.status, isLoading: false });
      return result;
    } catch (error) {
      // Revert on error
      set({ deviceStatus: prevStatus, isLoading: false });
      get().setError(getApiErrorMessage(error, "Failed to update LED."));
      return null;
    }
  },

  updateServo: async (angle) => {
    set({ isLoading: true });
    try {
      const result = await setServoAngle(angle);
      set({ deviceStatus: result.status, isLoading: false });
      return result;
    } catch (error) {
      set({ isLoading: false });
      get().setError(getApiErrorMessage(error, "Failed to update servo."));
      return null;
    }
  },
}));
