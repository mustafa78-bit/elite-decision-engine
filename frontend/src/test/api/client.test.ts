import { describe, expect, it, vi } from "vitest";

process.env.VITE_API_URL = "http://localhost:8000";

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

describe("setUnauthorizedHandler", () => {
  it("calls the registered handler on a 401 response", async () => {
    const { apiFetch, setUnauthorizedHandler } = await import("../../api/client");
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    }));

    await expect(apiFetch("/test")).rejects.toThrow("API error 401");
    expect(handler).toHaveBeenCalledOnce();

    setUnauthorizedHandler(null);
  });

  it("does NOT call the handler on a 404 or 500 response", async () => {
    const { apiFetch, apiFetchText, setUnauthorizedHandler } = await import("../../api/client");
    const handler = vi.fn();
    setUnauthorizedHandler(handler);

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
    }));
    await expect(apiFetch("/test")).rejects.toThrow("API error 404");

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    }));
    await expect(apiFetchText("/test")).rejects.toThrow("API error 500");

    expect(handler).not.toHaveBeenCalled();
    setUnauthorizedHandler(null);
  });

  it("does nothing on a 401 when no handler is registered", async () => {
    const { apiFetch, setUnauthorizedHandler } = await import("../../api/client");
    setUnauthorizedHandler(null);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    }));

    await expect(apiFetch("/test")).rejects.toThrow("API error 401");
  });
});
