import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET, POST } from "./route";

// Build the route-handler `ctx` whose params resolve to the catch-all path segments.
function ctx(path: string[]) {
  return { params: Promise.resolve({ path }) };
}

function mockUpstream(body: BodyInit | null, init: ResponseInit): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(body, init)),
  );
}

const fetchMock = () => vi.mocked(fetch);

describe("BFF proxy route", () => {
  beforeEach(() => {
    // API_BASE_URL unset → defaults to http://localhost:8000; UPSTREAM_AUTH unset → no id token.
    delete process.env.API_BASE_URL;
    delete process.env.UPSTREAM_AUTH;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("forwards method, path and query to the upstream and returns its status/body", async () => {
    mockUpstream(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });

    const req = new NextRequest("http://app.test/api/customers?search=alice&page=2");
    const res = await GET(req, ctx(["customers"]));

    expect(fetchMock()).toHaveBeenCalledTimes(1);
    const [url, opts] = fetchMock().mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/customers?search=alice&page=2");
    expect(opts?.method).toBe("GET");
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true });
  });

  it("passes SSE responses through with streaming headers", async () => {
    mockUpstream("data: hello\n\n", {
      status: 200,
      headers: { "content-type": "text/event-stream" },
    });

    const req = new NextRequest("http://app.test/api/customers/CUST-1/pitch", { method: "POST" });
    const res = await POST(req, ctx(["customers", "CUST-1", "pitch"]));

    expect(res.headers.get("content-type")).toContain("text/event-stream");
    expect(res.headers.get("cache-control")).toBe("no-cache, no-transform");
    expect(res.headers.get("x-accel-buffering")).toBe("no");
    expect(await res.text()).toBe("data: hello\n\n");
  });

  it("forwards the request body on POST", async () => {
    mockUpstream(JSON.stringify({ batch_id: 7 }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });

    const req = new NextRequest("http://app.test/api/pitches/bulk", {
      method: "POST",
      body: JSON.stringify({ customer_ids: ["CUST-1"], force: true }),
      headers: { "content-type": "application/json" },
    });
    await POST(req, ctx(["pitches", "bulk"]));

    const [, opts] = fetchMock().mock.calls[0];
    expect(opts?.body).toBe(JSON.stringify({ customer_ids: ["CUST-1"], force: true }));
  });

  it("rejects path traversal without hitting the upstream", async () => {
    vi.stubGlobal("fetch", vi.fn());

    const req = new NextRequest("http://app.test/api/../secret");
    const res = await GET(req, ctx(["..", "secret"]));

    expect(res.status).toBe(404);
    expect(fetchMock()).not.toHaveBeenCalled();
  });

  it("propagates the client abort signal to the upstream fetch", async () => {
    mockUpstream(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });

    const req = new NextRequest("http://app.test/api/customers");
    await GET(req, ctx(["customers"]));

    const [, opts] = fetchMock().mock.calls[0];
    expect(opts?.signal).toBeDefined();
    expect(opts?.signal).toBe(req.signal);
  });
});
