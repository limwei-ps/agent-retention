// BFF proxy: browser → this route handler → FastAPI. Keeps the backend URL server-side (one origin,
// no CORS, no key leakage). A single catch-all forwards every method/query/body to the API and passes
// the upstream response through unbuffered — so SSE (single-pitch POST, bulk GET /stream) streams
// token-by-token instead of buffering.

import { type NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

function forwardRequestHeaders(source: Headers): Headers {
  const out = new Headers();
  const contentType = source.get("content-type");
  const accept = source.get("accept");
  if (contentType) out.set("content-type", contentType);
  if (accept) out.set("accept", accept);
  return out;
}

async function proxy(req: NextRequest, segments: string[]): Promise<Response> {
  const target = `${API_BASE_URL}/api/${segments.join("/")}${req.nextUrl.search}`;
  const hasBody = req.method !== "GET" && req.method !== "HEAD";

  const upstream = await fetch(target, {
    method: req.method,
    headers: forwardRequestHeaders(req.headers),
    body: hasBody ? await req.text() : undefined,
    redirect: "manual",
  });

  const headers = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (contentType?.includes("text/event-stream")) {
    headers.set("cache-control", "no-cache, no-transform");
    headers.set("x-accel-buffering", "no");
  } else {
    const cacheControl = upstream.headers.get("cache-control");
    if (cacheControl) headers.set("cache-control", cacheControl);
  }

  // Pass the upstream body straight through (a ReadableStream) so streaming responses stay streaming.
  return new Response(upstream.body, { status: upstream.status, headers });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx): Promise<Response> {
  return proxy(req, (await ctx.params).path);
}

export async function POST(req: NextRequest, ctx: Ctx): Promise<Response> {
  return proxy(req, (await ctx.params).path);
}
