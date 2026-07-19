"use client";

import type { ReactNode } from "react";

import { FiltersProvider } from "./FiltersProvider";
import { PitchProvider } from "./PitchProvider";
import { QueryProvider } from "./query-provider";

/**
 * Composes all client-side context providers: TanStack Query for server state, FiltersProvider for
 * the customer-list query state, PitchProvider for the per-pitch streaming state machine.
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <FiltersProvider>
        <PitchProvider>{children}</PitchProvider>
      </FiltersProvider>
    </QueryProvider>
  );
}
