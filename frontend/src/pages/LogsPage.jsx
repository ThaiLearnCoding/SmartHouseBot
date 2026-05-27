import { useCallback, useEffect, useState } from "react";
import { fetchDeviceCommandLogs, fetchVoiceLogs } from "../services/auditApi";
import { getApiErrorMessage } from "../lib/axios";
import { formatCommandType, formatIntent, formatLogSource } from "../lib/utils";

function formatLogTime(value) {
  if (!value) return "—";
  const parsed = new Date(value.includes("T") ? value : `${value.replace(" ", "T")}Z`);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("vi-VN");
}

function formatPayload(payload) {
  if (!payload || typeof payload !== "object") return "—";
  if ("on" in payload) return payload.on ? "Bật" : "Tắt";
  if ("angle" in payload) return `${payload.angle}°`;
  return JSON.stringify(payload);
}

function StatusBadge({ success }) {
  return (
    <span
      className="bmw-caption px-2 py-1"
      style={{
        backgroundColor: success ? "rgba(28, 105, 212, 0.12)" : "rgba(220, 38, 38, 0.12)",
        color: success ? "var(--color-primary)" : "#b91c1c",
      }}
    >
      {success ? "Thành công" : "Lỗi"}
    </span>
  );
}

function CommandLogTable({ items, total }) {
  return (
    <div className="bmw-card" style={{ border: "1px solid var(--color-hairline)" }}>
      <div className="bmw-card-header">
        <h2 className="bmw-card-title">Lệnh thiết bị</h2>
        <p className="bmw-body-sm" style={{ color: "var(--color-muted)" }}>
          LED / Servo từ web và giọng nói — {total} bản ghi
        </p>
      </div>
      <div className="overflow-x-auto mt-6">
        {items.length === 0 ? (
          <p className="bmw-body-sm" style={{ color: "var(--color-muted)" }}>
            Chưa có lệnh nào được ghi.
          </p>
        ) : (
          <table className="w-full text-left text-sm" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-hairline)" }}>
                <th className="py-3 pr-4 bmw-caption">Thời gian</th>
                <th className="py-3 pr-4 bmw-caption">Lệnh</th>
                <th className="py-3 pr-4 bmw-caption">Giá trị</th>
                <th className="py-3 pr-4 bmw-caption">Nguồn</th>
                <th className="py-3 bmw-caption">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} style={{ borderBottom: "1px solid var(--color-hairline)" }}>
                  <td className="py-3 pr-4 whitespace-nowrap">{formatLogTime(row.created_at)}</td>
                  <td className="py-3 pr-4">{formatCommandType(row.command_type)}</td>
                  <td className="py-3 pr-4">{formatPayload(row.payload)}</td>
                  <td className="py-3 pr-4">{formatLogSource(row.source)}</td>
                  <td className="py-3">
                    <StatusBadge success={row.success} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function VoiceLogTable({ items, total }) {
  return (
    <div className="bmw-card" style={{ border: "1px solid var(--color-hairline)" }}>
      <div className="bmw-card-header">
        <h2 className="bmw-card-title">Hội thoại giọng nói</h2>
        <p className="bmw-body-sm" style={{ color: "var(--color-muted)" }}>
          Lời nói, ý định, phản hồi — {total} bản ghi
        </p>
      </div>
      <div className="overflow-x-auto mt-6">
        {items.length === 0 ? (
          <p className="bmw-body-sm" style={{ color: "var(--color-muted)" }}>
            Chưa có hội thoại giọng nói nào được ghi.
          </p>
        ) : (
          <table className="w-full text-left text-sm" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-hairline)" }}>
                <th className="py-3 pr-4 bmw-caption">Thời gian</th>
                <th className="py-3 pr-4 bmw-caption">Lời nói</th>
                <th className="py-3 pr-4 bmw-caption">Ý định</th>
                <th className="py-3 pr-4 bmw-caption">Phản hồi</th>
                <th className="py-3 bmw-caption">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} style={{ borderBottom: "1px solid var(--color-hairline)" }}>
                  <td className="py-3 pr-4 whitespace-nowrap align-top">{formatLogTime(row.created_at)}</td>
                  <td className="py-3 pr-4 max-w-xs align-top">{row.transcript}</td>
                  <td className="py-3 pr-4 align-top">{formatIntent(row.intent)}</td>
                  <td className="py-3 pr-4 max-w-md align-top">{row.response_text}</td>
                  <td className="py-3 align-top">
                    <StatusBadge success={row.success} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default function LogsPage() {
  const [commands, setCommands] = useState([]);
  const [voiceLogs, setVoiceLogs] = useState([]);
  const [commandTotal, setCommandTotal] = useState(0);
  const [voiceTotal, setVoiceTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [commandData, voiceData] = await Promise.all([
        fetchDeviceCommandLogs(),
        fetchVoiceLogs(),
      ]);
      setCommands(commandData.items ?? []);
      setCommandTotal(commandData.total ?? 0);
      setVoiceLogs(voiceData.items ?? []);
      setVoiceTotal(voiceData.total ?? 0);
    } catch (err) {
      setError(getApiErrorMessage(err, "Không tải được nhật ký."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLogs();
    const interval = setInterval(loadLogs, 30000);
    return () => clearInterval(interval);
  }, [loadLogs]);

  return (
    <div className="flex flex-col">
      <div
        className="w-full flex items-center justify-center text-center"
        style={{
          backgroundColor: "var(--color-canvas)",
          padding: "80px 24px",
          borderBottom: "1px solid var(--color-hairline)",
        }}
      >
        <div className="max-w-[1440px] mx-auto">
          <h1 className="bmw-display-lg" style={{ color: "var(--color-ink)" }}>
            NHẬT KÝ HOẠT ĐỘNG
          </h1>
          <p className="bmw-body-sm mt-2" style={{ color: "var(--color-muted)" }}>
            Nhật ký lệnh thiết bị và hội thoại giọng nói
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-[1440px] w-full px-4 py-16 md:px-6 space-y-8">
        <div className="flex justify-end">
          <button
            type="button"
            className="bmw-button-secondary"
            onClick={loadLogs}
            disabled={isLoading}
          >
            {isLoading ? "Đang tải..." : "Làm mới"}
          </button>
        </div>

        {error && (
          <div
            className="bmw-body-sm px-4 py-3"
            style={{
              border: "1px solid #b91c1c",
              backgroundColor: "rgba(220, 38, 38, 0.08)",
              color: "#b91c1c",
            }}
          >
            {error}
          </div>
        )}

        <CommandLogTable items={commands} total={commandTotal} />
        <VoiceLogTable items={voiceLogs} total={voiceTotal} />
      </div>
    </div>
  );
}
