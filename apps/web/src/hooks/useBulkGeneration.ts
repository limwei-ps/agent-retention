"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { type QueryClient, useQuery, useQueryClient } from "@tanstack/react-query";

import { customersPath, fetchBulkStatus, openBulkStream, startBulk } from "@/lib/api";
import { parseSse } from "@/lib/sse";
import { useFilters } from "@/providers/FiltersProvider";

// The batch id is stashed in sessionStorage so an in-flight/complete batch survives navigating into a
// pitch detail and back (the dashboard page — and this hook — remount on that round trip). It is
// cleared when the customer-list query changes, so a filter/search change closes the now-stale panel
// instead of leaving a batch for the previous segment.
const BATCH_KEY = "retention.bulk.batchId";

function readStoredBatch(): number | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(BATCH_KEY);
  const n = raw ? Number(raw) : NaN;
  return Number.isFinite(n) ? n : null;
}

// Live progress comes from the SSE /stream, but the poll snapshot (counts + per-item items[]) is the
// single source of truth. SSE events just signal "something changed" → invalidate the poll query; the
// refetchInterval is the fallback if the stream drops. On done we also refresh the customer list so
// the table's pitch-status badges catch up.
async function consumeStream(batchId: number, qc: QueryClient): Promise<void> {
  try {
    const res = await openBulkStream(batchId);
    if (!res.body) return;
    for await (const frame of parseSse(res.body)) {
      void qc.invalidateQueries({ queryKey: ["bulk", batchId] });
      if (frame.event === "done") break;
    }
  } catch {
    // The polling query keeps the UI live even if the stream fails.
  } finally {
    void qc.invalidateQueries({ queryKey: ["bulk", batchId] });
    void qc.invalidateQueries({ queryKey: ["customers"] });
  }
}

export function useBulkGeneration() {
  const qc = useQueryClient();
  const { query } = useFilters();
  const [batchId, setBatchId] = useState<number | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Restore a batch left in sessionStorage (e.g. after opening a pitch and coming back). Client-only,
  // so it runs after mount — no SSR/hydration mismatch (initial render has no panel either way).
  useEffect(() => {
    // Hydration-safe: sessionStorage is client-only, so it must be read after mount (a lazy
    // initializer would mismatch SSR). One-time, harmless cascading render.
    const stored = readStoredBatch();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (stored !== null) setBatchId(stored);
  }, []);

  const poll = useQuery({
    queryKey: ["bulk", batchId],
    queryFn: () => fetchBulkStatus(batchId as number),
    enabled: batchId !== null,
    refetchInterval: (q) => (q.state.data?.complete ? false : 1500),
  });

  const start = useCallback(
    async (customerIds: string[], force = false) => {
      if (customerIds.length === 0) return;
      setStarting(true);
      setError(null);
      try {
        const { batch_id } = await startBulk({ customer_ids: customerIds, force });
        window.sessionStorage.setItem(BATCH_KEY, String(batch_id));
        setBatchId(batch_id);
        void consumeStream(batch_id, qc);
      } catch {
        setError("Couldn't start the batch. Check your connection and try again.");
      } finally {
        setStarting(false);
      }
    },
    [qc],
  );

  // Clear the batch when the list query actually changes (filter/search/sort/page). Compare against
  // the previous key rather than a first-render flag — Strict Mode double-invokes effects on mount
  // with the same ref, which would defeat a boolean guard and wipe the just-restored batch.
  const queryKey = customersPath(query);
  const lastKey = useRef(queryKey);
  useEffect(() => {
    if (lastKey.current === queryKey) return; // mount + Strict-Mode re-invoke: no real change
    lastKey.current = queryKey;
    window.sessionStorage.removeItem(BATCH_KEY);
    setBatchId(null);
    setError(null);
  }, [queryKey]);

  return { start, starting, status: poll.data, error };
}
