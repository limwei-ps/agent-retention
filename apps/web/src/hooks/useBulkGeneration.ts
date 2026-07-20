"use client";

import { useCallback, useState } from "react";

import { type QueryClient, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchBulkStatus, openBulkStream, startBulk } from "@/lib/api";
import { parseSse } from "@/lib/sse";

// Live progress comes from the SSE /stream, but the poll snapshot (counts + per-item items[]) is the
// single source of truth. So SSE events just signal "something changed" → invalidate the poll query;
// a refetchInterval is the fallback if the stream drops. On done we also refresh the customer list so
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
  const [batchId, setBatchId] = useState<number | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
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

  return { start, starting, status: query.data, error };
}
