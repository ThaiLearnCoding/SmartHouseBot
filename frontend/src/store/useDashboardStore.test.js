import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/dashboardApi", () => ({
  fetchHealth: vi.fn(),
  fetchLatestTelemetry: vi.fn(),
  fetchTelemetryHistory: vi.fn(),
  fetchDeviceStatus: vi.fn(),
  setLedState: vi.fn(),
  setServoAngle: vi.fn(),
}));

import {
  fetchDeviceStatus,
  fetchHealth,
  fetchLatestTelemetry,
  fetchTelemetryHistory,
  setLedState,
  setServoAngle,
} from "../services/dashboardApi";
import { useDashboardStore, resetHistoryBuffers } from "./useDashboardStore";

describe("useDashboardStore", () => {
  beforeEach(() => {
    resetHistoryBuffers();
    useDashboardStore.setState({
      health: null,
      latest: null,
      deviceStatus: null,
      history: [],
      rangeHours: 24,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it("loads dashboard data and falls back to latest device status when needed", async () => {
    fetchHealth.mockResolvedValue({ status: "ok" });
    fetchLatestTelemetry.mockResolvedValue({
      temperature: 28,
      humidity: 61,
      device_status: { led_on: true, servo_angle: 45, active_devices: 2, status_source: "telemetry" },
    });
    fetchTelemetryHistory.mockResolvedValue({ points: [{ timestamp: 1, temperature: 28, humidity: 61 }] });

    await useDashboardStore.getState().loadDashboard();

    const state = useDashboardStore.getState();
    expect(state.health).toEqual({ status: "ok" });
    expect(state.history).toHaveLength(1);
    expect(state.deviceStatus.led_on).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it("captures dashboard load failures", async () => {
    fetchHealth.mockRejectedValue(new Error("backend offline"));

    await useDashboardStore.getState().loadDashboard();

    expect(useDashboardStore.getState().error).toBe("backend offline");
    expect(useDashboardStore.getState().isLoading).toBe(false);
  });

  it("updates telemetry history for a selected range", async () => {
    fetchTelemetryHistory.mockResolvedValue({ points: [{ timestamp: 2, temperature: 30, humidity: 55 }] });

    await useDashboardStore.getState().setRangeHours(48);

    const state = useDashboardStore.getState();
    expect(state.rangeHours).toBe(48);
    expect(state.history[0].timestamp).toBe(2);
  });

  it("reuses cached history when switching back to a recent range", async () => {
    fetchTelemetryHistory.mockResolvedValue({
      points: [{ timestamp: 10, temperature: 27, humidity: 60 }],
      sample_interval_seconds: 150,
    });

    await useDashboardStore.getState().setRangeHours(24);
    await useDashboardStore.getState().setRangeHours(48);
    await useDashboardStore.getState().setRangeHours(24);

    expect(fetchTelemetryHistory).toHaveBeenCalledTimes(2);
    expect(useDashboardStore.getState().history[0].timestamp).toBe(10);
  });

  it("updates led and servo state from mutation responses", async () => {
    setLedState.mockResolvedValue({
      status: { led_on: true, servo_angle: 0, active_devices: 1, status_source: "cache" },
    });
    setServoAngle.mockResolvedValue({
      status: { led_on: true, servo_angle: 90, active_devices: 2, status_source: "cache" },
    });

    await useDashboardStore.getState().updateLed(true);
    expect(useDashboardStore.getState().deviceStatus.led_on).toBe(true);

    await useDashboardStore.getState().updateServo(90);
    expect(useDashboardStore.getState().deviceStatus.servo_angle).toBe(90);
  });

  it("stores device mutation errors without throwing from UI handlers", async () => {
    setLedState.mockRejectedValue(new Error("rate limited"));

    const result = await useDashboardStore.getState().updateLed(true);

    expect(result).toBeNull();
    expect(useDashboardStore.getState().error).toBe("rate limited");
  });
});
