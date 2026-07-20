"use client";

import { Spinner } from "@/components/ui/Spinner";
import { useDashboard } from "@/hooks/useDashboard";

export function DashboardSummary() {
  const { data, isLoading, isError } = useDashboard();

  if (isLoading) {
    return (
      <div className="text-ink-soft flex items-center gap-2 text-sm">
        <Spinner className="text-fibre" /> Loading summary…
      </div>
    );
  }
  if (isError || !data) {
    return <p className="text-danger-deep text-sm">Could not load the dashboard summary.</p>;
  }

  return (
    <section>
      <h2 className="text-ink-soft mb-2 font-mono text-[11px] tracking-widest uppercase">
        Expiring this month
      </h2>
      <div className="flex flex-wrap gap-3">
        <StatTile label="All plans" value={data.expiring_this_month} hero />
        {data.by_tier.map((tier) => (
          <StatTile key={tier.plan.id} label={tier.plan.name} value={tier.count} />
        ))}
      </div>
    </section>
  );
}

function StatTile({ label, value, hero }: { label: string; value: number; hero?: boolean }) {
  return (
    <div className="border-line bg-surface min-w-28 flex-1 rounded-xl border px-4 py-3">
      <div className={`font-display text-ink tnum font-semibold ${hero ? "text-3xl" : "text-2xl"}`}>
        {value}
      </div>
      <div className={`mt-1 h-0.5 w-6 rounded ${hero ? "bg-fibre" : "bg-line"}`} />
      <div className="text-ink-soft mt-2 truncate font-mono text-[11px] tracking-wide uppercase">
        {label}
      </div>
    </div>
  );
}
