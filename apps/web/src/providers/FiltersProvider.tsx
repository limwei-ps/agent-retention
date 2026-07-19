"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { CustomerQuery } from "@/lib/api";

type SortKey = NonNullable<CustomerQuery["sort"]>;
type Order = NonNullable<CustomerQuery["order"]>;

interface FiltersState {
  search: string;
  plan: string; // "" = all plans
  sort: SortKey;
  order: Order;
  page: number;
  pageSize: number;
}

const DEFAULTS: FiltersState = {
  search: "",
  plan: "",
  sort: "contract_end_date",
  order: "asc",
  page: 1,
  pageSize: 20,
};

interface FiltersContextValue extends FiltersState {
  query: CustomerQuery;
  setSearch: (v: string) => void;
  setPlan: (v: string) => void;
  setSort: (v: SortKey) => void;
  toggleOrder: () => void;
  setPage: (v: number) => void;
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
    return {
      ...state,
      query,
      setSearch: (v) => patch({ search: v }),
      setPlan: (v) => patch({ plan: v }),
      setSort: (v) => patch({ sort: v }),
      toggleOrder: () => patch({ order: state.order === "asc" ? "desc" : "asc" }),
      setPage: (v) => patch({ page: v }, false),
    };
  }, [state, patch]);

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters(): FiltersContextValue {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error("useFilters must be used within <FiltersProvider>");
  return ctx;
}
