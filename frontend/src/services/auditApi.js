import { axiosInstance } from "../lib/axios";

export async function fetchDeviceCommandLogs(limit = 50, offset = 0) {
  const { data } = await axiosInstance.get("/audit/commands", {
    params: { limit, offset },
  });
  return data;
}

export async function fetchVoiceLogs(limit = 50, offset = 0) {
  const { data } = await axiosInstance.get("/audit/voice", {
    params: { limit, offset },
  });
  return data;
}
