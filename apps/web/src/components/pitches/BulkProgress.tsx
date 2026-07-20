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
    <section className="border-line bg-surface rounded-xl border p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-ink font-medium">
          Bulk generation — {status.completed} of {status.total}
          {status.complete ? " · done" : "…"}
        </span>
        <span className="text-ink-soft tnum font-mono text-[11px]">
          {status.succeeded} ok · {status.failed} failed
          {!status.live && " · (reconnected)"}
        </span>
      </div>

      <div
        className="bg-line h-1.5 w-full overflow-hidden rounded-full"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="bg-fibre h-full rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>

      <ul className="mt-3 flex max-h-48 flex-col gap-1 overflow-y-auto text-xs">
        {status.items.map((item) => (
          <li key={item.customer_id} className="flex items-center justify-between gap-2">
            <span className="text-ink-soft font-mono">{item.customer_id}</span>
            <span className="flex items-center gap-2">
              {item.error && (
                <span className="text-danger-deep max-w-40 truncate" title={item.error}>
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
