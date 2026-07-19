"use client";

import type { ReactNode } from "react";
import { QueryProvider } from "./query-provider";

/**
 * Composes all client-side context providers. Feature providers (per-pitch state
 * machine, filters) are added in later chunks and nested here.
 */
export function Providers({ children }: { children: ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>;
}
