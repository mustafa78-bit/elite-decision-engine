import { describe, expect, it, vi } from "vitest";
import { apiFetch, BASE_URL } from "../../api/client";

describe("apiFetch", () => {
  it("exports BASE_URL", () => {
    expect(BASE_URL).toBe("http://localhost:8000");
  });

  it("throws ApiError on non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
    }));
    await expect(apiFetch("/test")).rejects.toThrow("API error 404");
  });

  it("parses JSON on success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: "ok" }),
    }));
    const result = await apiFetch<{ data: string }>("/test");
    expect(result.data).toBe("ok");
  });
});
