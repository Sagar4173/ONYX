import { describe, it, expect, vi, beforeEach } from "vitest";
import { mlAPI, api } from "./api";

describe("mlAPI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches the ML status", async () => {
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({
      data: { model_trained: false, isolation_forest_enabled: false },
    });

    const result = await mlAPI.getStatus();

    expect(getSpy).toHaveBeenCalledWith("/ml/status");
    expect(result).toEqual({ model_trained: false, isolation_forest_enabled: false });
  });

  it("trains with a long per-request timeout and propagates errors", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({
      data: { model_id: "m1", training_data_size: 42 },
    });

    const result = await mlAPI.train();

    expect(postSpy).toHaveBeenCalledWith("/ml/train", null, { timeout: 300000 });
    expect(result).toEqual({ model_id: "m1", training_data_size: 42 });

    postSpy.mockRejectedValue(new Error("boom"));
    await expect(mlAPI.train()).rejects.toThrow("boom");
  });

  it("fetches the anomaly dashboard", async () => {
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({
      data: { recent_alerts: [], anomaly_detection_status: "training_required" },
    });

    const result = await mlAPI.getAnomalies();

    expect(getSpy).toHaveBeenCalledWith("/ml/anomalies");
    expect(result).toEqual({ recent_alerts: [], anomaly_detection_status: "training_required" });
  });

  it("propagates status errors", async () => {
    vi.spyOn(api, "get").mockRejectedValue(new Error("network"));

    await expect(mlAPI.getStatus()).rejects.toThrow("network");
  });
});
