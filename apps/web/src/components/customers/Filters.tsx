"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { useDashboard } from "@/hooks/useDashboard";
import { useFilters } from "@/providers/FiltersProvider";

const SORTS: { value: "contract_end_date" | "tenure" | "avg_gb"; label: string }[] = [
  { value: "contract_end_date", label: "Expiry date" },
  { value: "tenure", label: "Tenure" },
  { value: "avg_gb", label: "Avg usage" },
];

export function Filters() {
  const { search, plan, sort, order, setSearch, setPlan, setSort, toggleOrder } = useFilters();
  const { data: dashboard } = useDashboard();

  // Debounce the text input so each keystroke doesn't refetch.
  const [term, setTerm] = useState(search);
  useEffect(() => {
    const id = setTimeout(() => setSearch(term), 300);
    return () => clearTimeout(id);
  }, [term, setSearch]);

  const fieldClass =
    "rounded border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800";

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
    </div>
  );
}
