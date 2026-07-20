"use client";

import { Spinner } from "@/components/ui/Spinner";
import { StatTile } from "@/components/ui/StatTile";
import { useDashboard } from "@/hooks/useDashboard";
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
