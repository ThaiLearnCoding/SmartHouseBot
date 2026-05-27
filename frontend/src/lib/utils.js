const STATUS_SOURCE_LABELS = {
  coreiot_attributes: "Thuộc tính CoreIoT",
  telemetry: "Telemetry CoreIoT",
  cache: "Bộ nhớ tạm",
  unknown: "Không rõ",
};

const COMMAND_TYPE_LABELS = {
  led: "Đèn LED",
  servo: "Servo",
};

const LOG_SOURCE_LABELS = {
  web: "Web",
  voice: "Giọng nói",
};

const INTENT_LABELS = {
  set_led: "Bật/tắt đèn",
  set_servo: "Điều chỉnh servo",
  device_status: "Trạng thái thiết bị",
  read_sensor: "Đọc cảm biến",
  house_summary: "Tình trạng nhà",
  need_clarification: "Cần làm rõ",
  out_of_domain: "Ngoài phạm vi",
  chitchat: "Trò chuyện",
  unknown: "Không xác định",
  empty: "Rỗng",
};

export function formatTemperature(value) {
  return value == null ? "—" : `${Number(value).toFixed(2)} °C`;
}

export function formatHumidity(value) {
  return value == null ? "—" : `${Number(value).toFixed(2)}%`;
}

export function formatSensorValue(value) {
  return value == null ? "—" : Number(value).toFixed(2);
}

export function formatTimestamp(isoTime) {
  if (!isoTime) return "—";
  return new Date(isoTime).toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatChartTimestamp(timestampMs, rangeHours = 24) {
  if (timestampMs == null) return "—";
  const date = new Date(timestampMs);
  if (Number.isNaN(date.getTime())) return "—";
  if (rangeHours > 12) {
    return date.toLocaleString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return date.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatChartTooltipTime(timestampMs) {
  if (timestampMs == null) return "—";
  const date = new Date(timestampMs);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatStatusSource(source) {
  if (!source) return "Không rõ";
  return STATUS_SOURCE_LABELS[source] ?? source;
}

export function formatCommandType(type) {
  if (!type) return "—";
  return COMMAND_TYPE_LABELS[type] ?? type;
}

export function formatLogSource(source) {
  if (!source) return "—";
  return LOG_SOURCE_LABELS[source] ?? source;
}

export function formatIntent(intent) {
  if (!intent) return "—";
  return INTENT_LABELS[intent] ?? intent;
}
