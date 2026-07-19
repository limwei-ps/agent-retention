"use client";

import { openPitchStream } from "@/lib/api";
import { parseSse } from "@/lib/sse";
import type { PitchStreamEvent } from "@/types/api";

/**
 * Consume the single-pitch SSE pass-through as typed events. It's a POST stream, so we read the
 * fetch body via `parseSse` rather than using `EventSource`. Yields token/regenerating/fallback/
 * done/error in order; throws if the stream can't be opened.
 */
export async function* streamPitch(id: string, force: boolean): AsyncGenerator<PitchStreamEvent> {
  const res = await openPitchStream(id, force);
  if (!res.ok || !res.body) throw new Error(`pitch stream failed (${res.status})`);
  for await (const frame of parseSse(res.body)) {
    yield { event: frame.event, data: JSON.parse(frame.data) } as PitchStreamEvent;
  }
}
