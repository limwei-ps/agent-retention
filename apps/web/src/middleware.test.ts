import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { __resetRateLimit, middleware } from "./middleware";

const PASSWORD = "s3cret";
const basic = (pw: string) => `Basic ${btoa(`dev:${pw}`)}`;

function req(path: string, headers: Record<string, string> = {}): NextRequest {
  return new NextRequest(`http://app.test${path}`, { headers });
}

describe("middleware gate + rate limit", () => {
  beforeEach(() => {
    process.env.APP_PASSWORD = PASSWORD;
    process.env.RATE_LIMIT_PER_MIN = "1000"; // high by default; the RL test overrides it
    __resetRateLimit();
  });
  afterEach(() => {
    delete process.env.APP_PASSWORD;
    delete process.env.RATE_LIMIT_PER_MIN;
  });

  it("401s a request with no credentials and asks for Basic auth", () => {
    const res = middleware(req("/"));
    expect(res.status).toBe(401);
    expect(res.headers.get("WWW-Authenticate")).toContain("Basic");
  });

  it("401s a wrong password", () => {
    const res = middleware(req("/", { authorization: basic("nope") }));
    expect(res.status).toBe(401);
  });

  it("passes a correct password", () => {
    const res = middleware(req("/", { authorization: basic(PASSWORD) }));
    expect(res.status).not.toBe(401);
    expect(res.status).not.toBe(429);
  });

  it("is fully bypassed when APP_PASSWORD is unset (local dev)", () => {
    delete process.env.APP_PASSWORD;
    const res = middleware(req("/", {}));
    expect(res.status).not.toBe(401);
  });

  it("429s the same IP past the per-IP limit on /api/*", () => {
    process.env.RATE_LIMIT_PER_MIN = "2";
    const headers = { authorization: basic(PASSWORD), "x-forwarded-for": "1.2.3.4" };
    expect(middleware(req("/api/customers", headers)).status).not.toBe(429);
    expect(middleware(req("/api/customers", headers)).status).not.toBe(429);
    const third = middleware(req("/api/customers", headers));
    expect(third.status).toBe(429);
    expect(third.headers.get("Retry-After")).toBeTruthy();
  });

  it("rate-limits per IP independently", () => {
    process.env.RATE_LIMIT_PER_MIN = "1";
    const mk = (ip: string) =>
      middleware(req("/api/customers", { authorization: basic(PASSWORD), "x-forwarded-for": ip }));
    expect(mk("10.0.0.1").status).not.toBe(429);
    expect(mk("10.0.0.1").status).toBe(429); // second from same IP over limit
    expect(mk("10.0.0.2").status).not.toBe(429); // different IP unaffected
  });
});
