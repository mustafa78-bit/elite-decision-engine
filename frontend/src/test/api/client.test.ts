import { describe, expect, it, vi } from "vitest";

// @ts-ignore
const processEnv = typeof process !== "undefined" ? process.env : import.meta.env;
processEnv.VITE_API_URL = "http://localhost:8000";

describe("apiFetch", () => {
  it("reads BASE_URL from VITE_API_URL env", async () => {
    const { BASE_URL } = await import("../../api/client");
    expect(BASE_URL).toBe("http://localhost:8000");
  });

  it("throws ApiError on non-ok response", async () => {
    const { apiFetch } = await import("../../api/client");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
    }));
    await expect(apiFetch("/test")).rejects.toThrow("API error 404");
  });

  it("parses JSON on success", async () => {
    const { apiFetch } = await import("../../api/client");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: "ok" }),
    }));
    const result = await apiFetch<{ data: string }>("/test");
    expect(result.data).toBe("ok");
  });
});
