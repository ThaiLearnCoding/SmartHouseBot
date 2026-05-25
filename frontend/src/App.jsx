import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import HomePage from "./pages/HomePage";
import ControlsPage from "./pages/ControlsPage";
import TelemetryPage from "./pages/TelemetryPage";
import VoicePage from "./pages/VoicePage";
import LogsPage from "./pages/LogsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/controls" element={<ControlsPage />} />
          <Route path="/telemetry" element={<TelemetryPage />} />
          <Route path="/voice" element={<VoicePage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
