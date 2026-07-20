"use client";

import Link from "next/link";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatTile, type StatTileTone } from "@/components/ui/StatTile";
import type { BulkBatchStatus, BulkItemStatus } from "@/types/api";

type ItemStatus = BulkItemStatus["status"];

// Friendly labels aligned with PitchStatusBadge; `rank` sorts the list action-first (failures on top,
// finished last) so the agent's attention lands where work remains.
const ITEM: Record<ItemStatus, { label: string; tone: BadgeTone; rank: number }> = {
  failed: { label: "Failed", tone: "red", rank: 0 },
  running: { label: "Generating", tone: "blue", rank: 1 },
  pending: { label: "Queued", tone: "gray", rank: 2 },
  succeeded: { label: "Ready", tone: "green", rank: 3 },
};

const BUCKETS: { key: ItemStatus; label: string; tone: StatTileTone }[] = [
  { key: "pending", label: "Queued", tone: "neutral" },
  { key: "running", label: "Generating", tone: "fibre" },
  { key: "succeeded", label: "Ready", tone: "ok" },
  { key: "failed", label: "Failed", tone: "danger" },
];

export function BulkProgress({
  status,
  onRetryFailed,
}: {
  status: BulkBatchStatus;
  onRetryFailed?: () => void;
}) {
  const pct = status.total > 0 ? Math.round((status.completed / status.total) * 100) : 0;
  const counts: Record<ItemStatus, number> = {
    pending: status.pending,
    running: status.running,
    succeeded: status.succeeded,
    failed: status.failed,
  };
  const items = [...status.items].sort(
    (a, b) =>
      ITEM[a.status].rank - ITEM[b.status].rank || a.customer_id.localeCompare(b.customer_id),
  );

  return (
    <section
      role="region"
      aria-label="Bulk generation progress"
      className="border-line bg-surface overflow-hidden rounded-xl border"
    >
      {/* Signature fibre rail: light travels while generating, settles when the batch is done. */}
      <div
        className={status.complete ? "fibre-rule-idle" : "fibre-rule"}
        role="progressbar"
        aria-label="Bulk generation progress"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      />

      <div className="p-4">
        <div className="flex items-center justify-between">
          <span className="text-ink text-sm">
            <span className="font-display font-semibold">Bulk generation</span>
            <span className="text-ink-soft tnum ml-2 font-mono text-xs">
              {status.completed} / {status.total}
            </span>
          </span>
          {status.complete ? (
            <Badge tone={status.failed > 0 ? "amber" : "green"}>Done</Badge>
          ) : (
            <Badge tone={status.live ? "blue" : "gray"}>
              {status.live ? "Live" : "Reconnected"}
            </Badge>
          )}
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {BUCKETS.map((b) => (
            <StatTile key={b.key} label={b.label} value={counts[b.key]} tone={b.tone} />
          ))}
        </div>

        {status.complete && status.failed > 0 && onRetryFailed && (
          <div className="mt-3">
            <Button variant="secondary" onClick={onRetryFailed}>
              Retry {status.failed} failed
            </Button>
          </div>
        )}

        <ul className="divide-line/70 mt-3 flex max-h-56 flex-col divide-y overflow-y-auto text-xs">
          {items.map((item) => {
            const meta = ITEM[item.status];
            return (
              <li key={item.customer_id} className="flex items-center justify-between gap-2 py-1.5">
                <span className="flex min-w-0 items-center gap-2">
                  <span className="text-ink-soft font-mono">{item.customer_id}</span>
                  {item.status === "succeeded" && (
                    <Link
                      href={`/customers/${item.customer_id}`}
                      className="text-fibre-deep whitespace-nowrap hover:underline"
                    >
                      open pitch →
                    </Link>
                  )}
                  {item.error && (
                    <span className="text-danger-deep max-w-40 truncate" title={item.error}>
                      {item.error}
                    </span>
                  )}
                </span>
                <Badge tone={meta.tone}>{meta.label}</Badge>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
