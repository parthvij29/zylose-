import type {
  ApiEventsResponse,
  ApiStats,
  ApiAnalytics,
  ApiDevicesResponse,
  ApiPostEventRequest,
  ApiDashboardResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = (await res.json()) as { error?: string };
    throw new ApiError(
      res.status,
      body.error || `API error: ${res.status} ${res.statusText}`
    );
  }
  return res.json() as Promise<T>;
}

// ── Query parameter builder ───────────────────────────────────────────────

export interface EventQueryParams {
  page?: number;
  limit?: number;
  result?: string;
  device_id?: string;
  from?: string;
  to?: string;
  include_total?: boolean;
}

function buildQueryString(params?: EventQueryParams): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (entries.length === 0) return "";
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

// ── API Functions ─────────────────────────────────────────────────────────

export async function getEvents(
  params?: EventQueryParams
): Promise<ApiEventsResponse> {
  return apiFetch<ApiEventsResponse>(`/api/events${buildQueryString(params)}`);
}

export async function getStats(): Promise<ApiStats> {
  return apiFetch<ApiStats>("/api/stats");
}

export async function getAnalytics(): Promise<ApiAnalytics> {
  return apiFetch<ApiAnalytics>("/api/analytics");
}

export async function getDashboard(): Promise<ApiDashboardResponse> {
  return apiFetch<ApiDashboardResponse>("/api/dashboard");
}

export async function getDevices(): Promise<ApiDevicesResponse> {
  return apiFetch<ApiDevicesResponse>("/api/devices");
}

export async function postEvent(
  event: ApiPostEventRequest
): Promise<{ id: string; timestamp: string; status: string }> {
  return apiFetch<{ id: string; timestamp: string; status: string }>(
    "/api/events",
    {
      method: "POST",
      body: JSON.stringify(event),
    }
  );
}

export { ApiError };
