"use client";

import { BulkProgress } from "@/components/pitches/BulkProgress";
import { Button } from "@/components/ui/Button";
import { useBulkGeneration } from "@/hooks/useBulkGeneration";
import { useCustomers } from "@/hooks/useCustomers";
import { useFilters } from "@/providers/FiltersProvider";

// Bulk-generate the customers on the current page (the segment the agent is looking at). The bulk
// endpoint caps at 200; a page is <=100, so no extra guard needed here.
export function BulkGenerate() {
  const { query } = useFilters();
  const { data } = useCustomers(query); // shares the table's cached query — no extra fetch
  const { start, starting, status, error } = useBulkGeneration();

  const ids = data?.data.map((c) => c.id) ?? [];

  // A batch is in flight until the status snapshot reports complete — keep the button disabled the
  // whole time so a second click can't launch an overlapping batch for the same customers.
  const running = Boolean(status && !status.complete);
  const busy = starting || running;

  const failedIds =
    status?.items.filter((i) => i.status === "failed").map((i) => i.customer_id) ?? [];
  const retryFailed = () => start(failedIds, true);

  const label = busy
    ? `Generating… ${status?.completed ?? 0} of ${status?.total ?? ids.length}`
    : `Generate pitches for these ${ids.length}`;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Button onClick={() => start(ids)} disabled={busy || ids.length === 0}>
          {label}
        </Button>
        <span className="text-ink-soft text-xs">Runs on the current page (bulk max 200).</span>
      </div>
      {error && <p className="text-danger-deep text-sm">{error}</p>}
      {status && (
        <BulkProgress
          status={status}
          onRetryFailed={failedIds.length > 0 ? retryFailed : undefined}
        />
      )}
    </div>
  );
}
