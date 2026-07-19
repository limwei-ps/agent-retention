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
  const { start, starting, status } = useBulkGeneration();

  const ids = data?.data.map((c) => c.id) ?? [];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Button onClick={() => start(ids)} disabled={starting || ids.length === 0}>
          {starting ? "Starting…" : `Generate pitches for these ${ids.length}`}
        </Button>
        <span className="text-xs text-gray-400">Runs on the current page (bulk max 200).</span>
      </div>
      {status && <BulkProgress status={status} />}
    </div>
  );
}
