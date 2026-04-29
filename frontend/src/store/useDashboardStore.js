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

export const useDashboardStore = create((set, get) => ({
  health: null,
  latest: null,
  deviceStatus: null,
  history: [],
  rangeHours: 24,
  isLoading: false,
  error: null,

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
      set({ error: getApiErrorMessage(error, "Failed to load dashboard."), isLoading: false });
    }
  },

  setRangeHours: async (rangeHours) => {
    set({ rangeHours, isLoading: true, error: null });
    try {
      const history = await fetchTelemetryHistory(rangeHours);
      set({ history: history.points ?? [], isLoading: false });
    } catch (error) {
      set({ error: getApiErrorMessage(error, "Failed to load telemetry history."), isLoading: false });
    }
  },

  updateLed: async (on) => {
    try {
      const result = await setLedState(on);
      set({ deviceStatus: result.status });
      return result;
    } catch (error) {
      set({ error: getApiErrorMessage(error, "Failed to update LED.") });
      return null;
    }
  },

  updateServo: async (angle) => {
    try {
      const result = await setServoAngle(angle);
      set({ deviceStatus: result.status });
      return result;
    } catch (error) {
      set({ error: getApiErrorMessage(error, "Failed to update servo.") });
      return null;
    }
  },
}));
