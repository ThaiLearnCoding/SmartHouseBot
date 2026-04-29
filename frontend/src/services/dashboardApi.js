import { axiosInstance } from "../lib/axios";

export async function fetchHealth() {
  const { data } = await axiosInstance.get("/health");
  return data;
}

export async function fetchLatestTelemetry() {
  const { data } = await axiosInstance.get("/telemetry/latest");
  return data;
}

export async function fetchTelemetryHistory(rangeHours = 24) {
  const { data } = await axiosInstance.get("/telemetry/history", {
    params: { range_hours: rangeHours },
  });
  return data;
}

export async function fetchDeviceStatus() {
  const { data } = await axiosInstance.get("/devices/status");
  return data;
}

export async function setLedState(on) {
  const { data } = await axiosInstance.post("/devices/led", { on });
  return data;
}

export async function setServoAngle(angle) {
  const { data } = await axiosInstance.post("/devices/servo", { angle });
  return data;
}
