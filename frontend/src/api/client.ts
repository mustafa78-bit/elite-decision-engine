export const BASE_URL: string = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getWsBaseUrl(): string {
    return BASE_URL.replace(/^http/, "ws");
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = { "Content-Type": "application/json", ...getAuthHeaders(), ...init?.headers } as Record<string, string>;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// For endpoints that respond with raw text/pre-serialized content (e.g. a
// download) rather than something meant to be JSON-parsed -- apiFetch's
// unconditional res.json() would otherwise silently hand back a parsed
// object where a raw string was expected.
export async function apiFetchText(path: string, init?: RequestInit): Promise<string> {
  const headers = { "Content-Type": "application/json", ...getAuthHeaders(), ...init?.headers } as Record<string, string>;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API error ${res.status}: ${res.statusText}`);
  }
  return res.text();
}
