import { describe, it, expect, vi, beforeEach } from "vitest";
import { labelsAPI, api } from "./api";

describe("labelsAPI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts the label to the per-finding endpoint", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({
      data: { scan_id: "s1", finding_id: "f1", triage_label: "accepted" },
    });

    const result = await labelsAPI.setFindingLabel("s1", "f1", "accepted");

    expect(postSpy).toHaveBeenCalledWith("/reports/s1/findings/f1/label", {
      label: "accepted",
    });
    expect(result).toEqual({ scan_id: "s1", finding_id: "f1", triage_label: "accepted" });
  });

  it("sends untriaged to clear a label and propagates errors", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({
      data: { scan_id: "s1", finding_id: "f1", triage_label: null },
    });
    await labelsAPI.setFindingLabel("s1", "f1", "untriaged");
    expect(postSpy).toHaveBeenCalledWith("/reports/s1/findings/f1/label", {
      label: "untriaged",
    });

    vi.spyOn(api, "post").mockRejectedValue(new Error("boom"));
    await expect(labelsAPI.setFindingLabel("s1", "f1", "dismissed")).rejects.toThrow("boom");
  });
});
