import { beforeEach, describe, expect, it } from "vitest";
import {
  HistoryBuffer,
  applyHistoryResponse,
  readCachedHistory,
  resetHistoryBuffers,
} from "./historyBuffer";

describe("HistoryBuffer", () => {
  beforeEach(() => {
    resetHistoryBuffers();
  });

  it("keeps at most 576 points in RAM", () => {
    const buffer = new HistoryBuffer(576);
    const points = Array.from({ length: 600 }, (_, index) => ({
      timestamp: index,
      temperature: 20 + index,
    }));

    buffer.load({ points, sample_interval_seconds: 150 }, 24);

    expect(buffer.toArray()).toHaveLength(576);
    expect(buffer.toArray()[0].timestamp).toBe(24);
  });

  it("serves cached history per range without refetch", () => {
    applyHistoryResponse(
      { points: [{ timestamp: 1, temperature: 28 }], sample_interval_seconds: 150 },
      24,
    );

    const cached = readCachedHistory(24);
    expect(cached.history).toHaveLength(1);
    expect(cached.historySampleIntervalSeconds).toBe(150);
    expect(readCachedHistory(48)).toBeNull();
  });

  it("patches the latest bucket from live telemetry", () => {
    const buffer = new HistoryBuffer(576);
    buffer.load(
      {
        points: [
          { timestamp: 1000, temperature: 20, humidity: 50 },
          { timestamp: 2000, temperature: 21, humidity: 51 },
        ],
        sample_interval_seconds: 150,
      },
      24,
    );

    const updated = buffer.patchLatest({
      temperature: 29,
      humidity: 62,
      collected_at: 2000,
    });

    expect(updated.at(-1).temperature).toBe(29);
    expect(updated.at(-1).humidity).toBe(62);
    expect(updated[0].temperature).toBe(20);
  });
});
