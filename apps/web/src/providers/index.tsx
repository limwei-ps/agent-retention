"use client";

import type { ReactNode } from "react";

import { FiltersProvider } from "./FiltersProvider";
import { QueryProvider } from "./query-provider";

/**
 * Composes all client-side context providers: TanStack Query for server state,
 * FiltersProvider for the customer-list query state. (PitchProvider is added with the pitch panel.)
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <FiltersProvider>{children}</FiltersProvider>
    </QueryProvider>
  );
}
