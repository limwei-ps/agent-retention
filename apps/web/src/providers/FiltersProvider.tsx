"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { CustomerQuery } from "@/lib/api";

type SortKey = NonNullable<CustomerQuery["sort"]>;
type Order = NonNullable<CustomerQuery["order"]>;

// Bucket dropdowns map to the backend's numeric min/max range params. "" = any.
type Range = { min?: number; max?: number };
export const TENURE_BUCKETS: { value: string; label: string; range: Range }[] = [
  { value: "", label: "Any tenure", range: {} },
  { value: "0-12", label: "0–12 mo", range: { min: 0, max: 12 } },
  { value: "13-36", label: "13–36 mo", range: { min: 13, max: 36 } },
  { value: "37+", label: "37+ mo", range: { min: 37 } },
];
export const USAGE_BUCKETS: { value: string; label: string; range: Range }[] = [
  { value: "", label: "Any usage", range: {} },
  { value: "0-199", label: "<200 GB", range: { min: 0, max: 199 } },
  { value: "200-499", label: "200–499 GB", range: { min: 200, max: 499 } },
  { value: "500+", label: "500+ GB", range: { min: 500 } },
];

const rangeOf = (buckets: { value: string; range: Range }[], value: string): Range =>
  buckets.find((b) => b.value === value)?.range ?? {};

interface FiltersState {
  search: string;
  plan: string; // "" = all plans
  sort: SortKey;
  order: Order;
  page: number;
  pageSize: number;
  expiring: boolean; // only contracts ending this calendar month
  tenureBucket: string; // "" = any
  usageBucket: string; // "" = any
}

const DEFAULTS: FiltersState = {
  search: "",
  plan: "",
  sort: "contract_end_date",
  order: "asc",
  page: 1,
  pageSize: 10,
  expiring: false,
  tenureBucket: "",
  usageBucket: "",
};

interface FiltersContextValue extends FiltersState {
  query: CustomerQuery;
  setSearch: (v: string) => void;
  setPlan: (v: string) => void;
  setSort: (v: SortKey) => void;
  toggleOrder: () => void;
  setPage: (v: number) => void;
  setExpiring: (v: boolean) => void;
  setTenure: (v: string) => void;
  setUsage: (v: string) => void;
  /** Dashboard-tile shortcut: filter to a plan (or "" for all) expiring this month. */
  focusExpiring: (plan: string) => void;
}

const FiltersContext = createContext<FiltersContextValue | null>(null);

export function FiltersProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<FiltersState>(DEFAULTS);

  // Any filter change resets to page 1; only paging preserves the rest.
  const patch = useCallback(
    (next: Partial<FiltersState>, resetPage = true) =>
      setState((prev) => ({ ...prev, ...next, page: resetPage ? 1 : (next.page ?? prev.page) })),
    [],
  );

  const value = useMemo<FiltersContextValue>(() => {
    const query: CustomerQuery = {
      sort: state.sort,
      order: state.order,
      page: state.page,
      page_size: state.pageSize,
    };
    if (state.search.trim()) query.search = state.search.trim();
    if (state.plan) query.plan = state.plan;
    if (state.expiring) query.expiring = true;
    const tenure = rangeOf(TENURE_BUCKETS, state.tenureBucket);
    if (tenure.min !== undefined) query.tenure_min = tenure.min;
    if (tenure.max !== undefined) query.tenure_max = tenure.max;
    const usage = rangeOf(USAGE_BUCKETS, state.usageBucket);
    if (usage.min !== undefined) query.usage_min = usage.min;
    if (usage.max !== undefined) query.usage_max = usage.max;
    return {
      ...state,
      query,
      setSearch: (v) => patch({ search: v }),
      setPlan: (v) => patch({ plan: v }),
      setSort: (v) => patch({ sort: v }),
      toggleOrder: () => patch({ order: state.order === "asc" ? "desc" : "asc" }),
      setPage: (v) => patch({ page: v }, false),
      setExpiring: (v) => patch({ expiring: v }),
      setTenure: (v) => patch({ tenureBucket: v }),
      setUsage: (v) => patch({ usageBucket: v }),
      focusExpiring: (plan) => patch({ plan, expiring: true }),
    };
  }, [state, patch]);

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters(): FiltersContextValue {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error("useFilters must be used within <FiltersProvider>");
  return ctx;
}
