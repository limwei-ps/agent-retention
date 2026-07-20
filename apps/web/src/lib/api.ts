// Browser-side API client. Every call hits the same-origin BFF proxy (`/api/...`), which forwards to
// FastAPI server-side — the backend URL never reaches the browser. JSON helpers return typed data;
// the two streaming endpoints return the raw `Response` so callers can read the SSE body.

import type {
  BulkBatchCreated,
  BulkBatchStatus,
  BulkPitchRequest,
  CustomerDetail,
  CustomerPage,
  DashboardSummary,
} from "@/types/api";

export interface CustomerQuery {
  search?: string;
  plan?: string;
  sort?: "tenure" | "avg_gb" | "contract_end_date";
  order?: "asc" | "desc";
  page?: number;
  page_size?: number;
  expiring?: boolean; // only contracts ending this calendar month
}

export function customersPath(q: CustomerQuery): string {
  const params = new URLSearchParams();
  if (q.search) params.set("search", q.search);
  if (q.plan) params.set("plan", q.plan);
  if (q.sort) params.set("sort", q.sort);
  if (q.order) params.set("order", q.order);
  if (q.page) params.set("page", String(q.page));
  if (q.page_size) params.set("page_size", String(q.page_size));
  if (q.expiring) params.set("expiring", "true");
  const qs = params.toString();
  return `/api/customers${qs ? `?${qs}` : ""}`;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { headers: { accept: "application/json" } });
  if (!res.ok) throw new Error(`GET ${path} failed (${res.status})`);
  return res.json() as Promise<T>;
}

export const fetchCustomers = (q: CustomerQuery): Promise<CustomerPage> =>
  getJson(customersPath(q));

export const fetchCustomerDetail = (id: string): Promise<CustomerDetail> =>
  getJson(`/api/customers/${encodeURIComponent(id)}`);

export const fetchDashboard = (): Promise<DashboardSummary> => getJson("/api/dashboard/summary");

export const fetchBulkStatus = (batchId: number): Promise<BulkBatchStatus> =>
  getJson(`/api/pitches/bulk/${batchId}`);

export async function startBulk(body: BulkPitchRequest): Promise<BulkBatchCreated> {
  const res = await fetch("/api/pitches/bulk", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`bulk start failed (${res.status})`);
  return res.json() as Promise<BulkBatchCreated>;
}

/** POST the single-pitch stream; returns the raw Response for SSE reading. `force` bypasses cache. */
export function openPitchStream(id: string, force: boolean): Promise<Response> {
  return fetch(`/api/customers/${encodeURIComponent(id)}/pitch`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "text/event-stream" },
    body: JSON.stringify({ force }),
  });
}

/** GET the bulk progress stream; returns the raw Response for SSE reading. */
export function openBulkStream(batchId: number): Promise<Response> {
  return fetch(`/api/pitches/bulk/${batchId}/stream`, {
    headers: { accept: "text/event-stream" },
  });
}
