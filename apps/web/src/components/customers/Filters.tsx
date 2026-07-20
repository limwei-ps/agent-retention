"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { useDashboard } from "@/hooks/useDashboard";
import { TENURE_BUCKETS, USAGE_BUCKETS, useFilters } from "@/providers/FiltersProvider";

const SORTS: { value: "contract_end_date" | "tenure" | "avg_gb"; label: string }[] = [
  { value: "contract_end_date", label: "Expiry date" },
  { value: "tenure", label: "Tenure" },
  { value: "avg_gb", label: "Avg usage" },
];

export function Filters() {
  const {
    search,
    plan,
    sort,
    order,
    expiring,
    tenureBucket,
    usageBucket,
    setSearch,
    setPlan,
    setSort,
    toggleOrder,
    setExpiring,
    setTenure,
    setUsage,
  } = useFilters();
  const { data: dashboard } = useDashboard();

  // Debounce the text input so each keystroke doesn't refetch.
  const [term, setTerm] = useState(search);
  useEffect(() => {
    const id = setTimeout(() => setSearch(term), 300);
    return () => clearTimeout(id);
  }, [term, setSearch]);

  const fieldClass =
    "rounded-md border border-line bg-surface px-2.5 py-1.5 text-sm text-ink placeholder:text-ink-soft/70 focus:border-fibre focus:outline-none focus:ring-2 focus:ring-fibre/30";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        type="search"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder="Search name or ID…"
        aria-label="Search customers"
        className={`${fieldClass} min-w-56 flex-1`}
      />
      <select
        value={plan}
        onChange={(e) => setPlan(e.target.value)}
        aria-label="Filter by plan"
        className={fieldClass}
      >
        <option value="">All plans</option>
        {dashboard?.by_tier.map((tier) => (
          <option key={tier.plan.id} value={tier.plan.id}>
            {tier.plan.name}
          </option>
        ))}
      </select>
      <select
        value={tenureBucket}
        onChange={(e) => setTenure(e.target.value)}
        aria-label="Filter by tenure"
        className={fieldClass}
      >
        {TENURE_BUCKETS.map((b) => (
          <option key={b.value} value={b.value}>
            {b.label}
          </option>
        ))}
      </select>
      <select
        value={usageBucket}
        onChange={(e) => setUsage(e.target.value)}
        aria-label="Filter by usage"
        className={fieldClass}
      >
        {USAGE_BUCKETS.map((b) => (
          <option key={b.value} value={b.value}>
            {b.label}
          </option>
        ))}
      </select>
      <select
        value={sort}
        onChange={(e) => setSort(e.target.value as (typeof SORTS)[number]["value"])}
        aria-label="Sort by"
        className={fieldClass}
      >
        {SORTS.map((s) => (
          <option key={s.value} value={s.value}>
            Sort: {s.label}
          </option>
        ))}
      </select>
      <Button variant="secondary" onClick={toggleOrder} aria-label="Toggle sort order">
        {order === "asc" ? "↑ Asc" : "↓ Desc"}
      </Button>
      {expiring && (
        <button
          type="button"
          onClick={() => setExpiring(false)}
          aria-label="Clear expiring-this-month filter"
          className="border-fibre/40 bg-fibre/10 text-fibre-deep hover:bg-fibre/20 inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium"
        >
          Expiring this month <span aria-hidden>✕</span>
        </button>
      )}
    </div>
  );
}
