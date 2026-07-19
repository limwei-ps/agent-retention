"use client";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import type { BulkBatchStatus, BulkItemStatus } from "@/types/api";

const ITEM_TONE: Record<BulkItemStatus["status"], BadgeTone> = {
  pending: "gray",
  running: "blue",
  succeeded: "green",
  failed: "red",
};

export function BulkProgress({ status }: { status: BulkBatchStatus }) {
  const pct = status.total > 0 ? Math.round((status.completed / status.total) * 100) : 0;

  return (
    <section className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium">
          Bulk generation — {status.completed} of {status.total}
          {status.complete ? " · done" : "…"}
        </span>
        <span className="text-xs text-gray-500 tabular-nums">
          {status.succeeded} ok · {status.failed} failed
          {!status.live && " · (reconnected)"}
        </span>
      </div>

      <div
        className="h-2 w-full overflow-hidden rounded bg-gray-100 dark:bg-gray-800"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="h-full bg-blue-500 transition-all" style={{ width: `${pct}%` }} />
      </div>

      <ul className="mt-3 flex max-h-48 flex-col gap-1 overflow-y-auto text-xs">
        {status.items.map((item) => (
          <li key={item.customer_id} className="flex items-center justify-between gap-2">
            <span className="font-mono text-gray-500">{item.customer_id}</span>
            <span className="flex items-center gap-2">
              {item.error && (
                <span className="max-w-40 truncate text-red-500" title={item.error}>
                  {item.error}
                </span>
              )}
              <Badge tone={ITEM_TONE[item.status]}>{item.status}</Badge>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
