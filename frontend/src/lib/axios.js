import axios from "axios";

export const axiosInstance = axios.create({
  baseURL: "/api",
  withCredentials: false,
});

export function getApiErrorMessage(error, fallback = "Request failed.") {
  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (error?.code === "ERR_NETWORK" || error?.message === "Network Error") {
    return "Backend API is unreachable. Start the FastAPI server on port 8000, or run npm run dev from the SmartHouseBot root.";
  }

  return error?.message || fallback;
}
