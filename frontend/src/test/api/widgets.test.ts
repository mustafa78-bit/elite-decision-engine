import { describe, expect, it, vi } from "vitest";
import { fetchKpiDetail } from "../../api/widgets";

describe("widgets API", () => {
  it("fetchKpiDetail calls /widgets/kpi/detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ kpis: [] }),
    }));
    const result = await fetchKpiDetail();
    expect(result.kpis).toEqual([]);
  });
});
