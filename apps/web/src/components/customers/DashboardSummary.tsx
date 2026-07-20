"use client";

import { Spinner } from "@/components/ui/Spinner";
import { useDashboard } from "@/hooks/useDashboard";
import { cn } from "@/lib/cn";
import { useFilters } from "@/providers/FiltersProvider";

export function DashboardSummary() {
  const { data, isLoading, isError } = useDashboard();
  const { plan, expiring, focusExpiring, setExpiring } = useFilters();

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

  // A tile is active when the list is filtered to its plan ("" = all) AND scoped to this month.
  const isActive = (tilePlan: string) => expiring && plan === tilePlan;
  const toggle = (tilePlan: string) =>
    isActive(tilePlan) ? setExpiring(false) : focusExpiring(tilePlan);

  return (
    <section>
      <h2 className="text-ink-soft mb-2 font-mono text-[11px] tracking-widest uppercase">
        Expiring this month
      </h2>
      <div className="flex flex-wrap gap-3">
        <StatTile
          label="All plans"
          value={data.expiring_this_month}
          hero
          active={isActive("")}
          onClick={() => toggle("")}
        />
        {data.by_tier.map((tier) => (
          <StatTile
            key={tier.plan.id}
            label={tier.plan.name}
            value={tier.count}
            active={isActive(tier.plan.id)}
            onClick={() => toggle(tier.plan.id)}
          />
        ))}
      </div>
    </section>
  );
}

function StatTile({
  label,
  value,
  hero,
  active,
  onClick,
}: {
  label: string;
  value: number;
  hero?: boolean;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "focus-visible:ring-fibre min-w-28 flex-1 rounded-xl border px-4 py-3 text-left transition focus-visible:ring-2 focus-visible:outline-none",
        active
          ? "border-fibre bg-fibre/8 ring-fibre/40 ring-1"
          : "border-line bg-surface hover:border-fibre/50",
      )}
    >
      <div
        className={cn("font-display text-ink tnum font-semibold", hero ? "text-3xl" : "text-2xl")}
      >
        {value}
      </div>
      <div className={cn("mt-1 h-0.5 w-6 rounded", active || hero ? "bg-fibre" : "bg-line")} />
      <div className="text-ink-soft mt-2 truncate font-mono text-[11px] tracking-wide uppercase">
        {label}
      </div>
    </button>
  );
}
