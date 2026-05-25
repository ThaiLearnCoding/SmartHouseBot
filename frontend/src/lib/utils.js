export function formatTemperature(value) {
  return value == null ? "--" : `${Number(value).toFixed(1)} C`;
}

export function formatHumidity(value) {
  return value == null ? "--" : `${Number(value).toFixed(1)}%`;
}

export function formatTimestamp(isoTime) {
  if (!isoTime) return "--";
  return new Date(isoTime).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}
