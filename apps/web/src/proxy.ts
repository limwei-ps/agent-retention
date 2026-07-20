// Edge gate for the public demo (auth is out of scope; this is a lightweight shared-secret gate).
// Two protections, active only when APP_PASSWORD is set (so local dev / CI / Playwright stay open):
//   1. HTTP Basic Auth — one shared password; browser shows its native prompt; gates every route
//      incl. the /api/* BFF proxy (the only path to the private API + billable LLM).
//   2. Per-IP request rate limit on /api/* — the request-layer complement to the bulk semaphore.
// In-process state is coherent because the service runs at --max-instances=1; a wider fleet would
// need a shared store (Redis) — noted in docs/take-home-plan.md §8.

import { NextResponse, type NextRequest } from "next/server";

const REALM = 'Basic realm="Retention (dev)"';
const WINDOW_MS = 60_000;

function rateLimitPerMin(): number {
  const n = Number(process.env.RATE_LIMIT_PER_MIN);
  return Number.isFinite(n) && n > 0 ? n : 60;
}

// Constant-time string compare (avoids leaking the password length/prefix via timing).
function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function passwordFromBasicHeader(header: string | null): string | null {
  if (!header?.startsWith("Basic ")) return null;
  try {
    const decoded = atob(header.slice(6)); // "user:pass"
    const sep = decoded.indexOf(":");
    return sep === -1 ? decoded : decoded.slice(sep + 1); // username ignored
  } catch {
    return null;
  }
}

function unauthorized(): NextResponse {
  return new NextResponse("Authentication required.", {
    status: 401,
    headers: { "WWW-Authenticate": REALM },
  });
}

// Fixed-window per-IP counters (module state persists within the single instance).
const hits = new Map<string, { count: number; resetAt: number }>();

function rateLimited(ip: string, now: number): { limited: boolean; retryAfter: number } {
  const limit = rateLimitPerMin();
  const bucket = hits.get(ip);
  if (!bucket || now >= bucket.resetAt) {
    hits.set(ip, { count: 1, resetAt: now + WINDOW_MS });
    return { limited: false, retryAfter: 0 };
  }
  bucket.count += 1;
  if (bucket.count > limit) {
    return { limited: true, retryAfter: Math.ceil((bucket.resetAt - now) / 1000) };
  }
  return { limited: false, retryAfter: 0 };
}

/** Test-only: clear the in-process rate-limit state. */
export function __resetRateLimit(): void {
  hits.clear();
}

export function proxy(req: NextRequest): NextResponse {
  const password = process.env.APP_PASSWORD;
  if (!password) return NextResponse.next(); // gate disabled (local dev / CI / e2e)

  // 1) Basic Auth gate — all routes.
  const supplied = passwordFromBasicHeader(req.headers.get("authorization"));
  if (supplied === null || !safeEqual(supplied, password)) return unauthorized();

  // 2) Per-IP rate limit — only the /api/* surface that reaches the backend/LLM.
  if (req.nextUrl.pathname.startsWith("/api/")) {
    const ip = (req.headers.get("x-forwarded-for") ?? "unknown").split(",")[0].trim() || "unknown";
    const { limited, retryAfter } = rateLimited(ip, Date.now());
    if (limited) {
      return new NextResponse("Too many requests.", {
        status: 429,
        headers: { "Retry-After": String(retryAfter) },
      });
    }
  }

  return NextResponse.next();
}

// Gate everything except Next's static assets and the favicon.
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
