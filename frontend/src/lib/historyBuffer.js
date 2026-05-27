export const HISTORY_BUCKET_COUNT = 576;
export const HISTORY_CACHE_TTL_MS = 25_000;

const buffersByRange = new Map();

export class HistoryBuffer {
  constructor(maxSize = HISTORY_BUCKET_COUNT) {
    this.maxSize = maxSize;
    this.points = [];
    this.sampleIntervalSeconds = 20;
    this.rangeHours = null;
    this.fetchedAt = 0;
  }

  load(response, rangeHours) {
    this.points = (response?.points ?? []).slice(-this.maxSize);
    this.sampleIntervalSeconds = response?.sample_interval_seconds ?? 20;
    this.rangeHours = rangeHours;
    this.fetchedAt = Date.now();
    return this.toArray();
  }

  isFresh(rangeHours, ttlMs = HISTORY_CACHE_TTL_MS) {
    return (
      this.rangeHours === rangeHours &&
      this.points.length > 0 &&
      Date.now() - this.fetchedAt < ttlMs
    );
  }

  patchLatest(latest) {
    if (!this.points.length || !latest) {
      return this.toArray();
    }

    const lastIndex = this.points.length - 1;
    const current = this.points[lastIndex];
    this.points[lastIndex] = {
      ...current,
      timestamp: latest.collected_at ?? current.timestamp,
      temperature: latest.temperature ?? current.temperature,
      humidity: latest.humidity ?? current.humidity,
    };
    return this.toArray();
  }

  toArray() {
    return this.points;
  }
}

export function getHistoryBuffer(rangeHours) {
  if (!buffersByRange.has(rangeHours)) {
    buffersByRange.set(rangeHours, new HistoryBuffer());
  }
  return buffersByRange.get(rangeHours);
}

export function resetHistoryBuffers() {
  buffersByRange.clear();
}

export function applyHistoryResponse(response, rangeHours) {
  const buffer = getHistoryBuffer(rangeHours);
  const points = buffer.load(response, rangeHours);
  return {
    history: points,
    historySampleIntervalSeconds: buffer.sampleIntervalSeconds,
  };
}

export function readCachedHistory(rangeHours) {
  const buffer = getHistoryBuffer(rangeHours);
  if (!buffer.isFresh(rangeHours)) {
    return null;
  }
  return {
    history: buffer.toArray(),
    historySampleIntervalSeconds: buffer.sampleIntervalSeconds,
  };
}
