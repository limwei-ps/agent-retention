import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useBulkGeneration } from "@/hooks/useBulkGeneration";
import { FiltersProvider, useFilters } from "@/providers/FiltersProvider";
import { QueryProvider } from "@/providers/query-provider";
import * as api from "@/lib/api";
import type { BulkBatchStatus } from "@/types/api";

vi.mock("@/lib/api", async (orig) => ({
  ...(await orig<typeof import("@/lib/api")>()), // keep the real customersPath (reset key)
  startBulk: vi.fn(),
  fetchBulkStatus: vi.fn(),
  openBulkStream: vi.fn(),
}));

const DONE: BulkBatchStatus = {
  batch_id: 7,
  total: 1,
  completed: 1,
  succeeded: 1,
  failed: 0,
  running: 0,
  pending: 0,
  complete: true,
  live: true,
  items: [{ customer_id: "CUST-1", status: "succeeded", pitch_id: 3, error: null }],
};

function wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <FiltersProvider>{children}</FiltersProvider>
    </QueryProvider>
  );
}

const useHarness = () => ({ bulk: useBulkGeneration(), filters: useFilters() });

describe("useBulkGeneration", () => {
  beforeEach(() => {
    vi.mocked(api.startBulk).mockResolvedValue({ batch_id: 7, total: 1 });
    vi.mocked(api.fetchBulkStatus).mockResolvedValue(DONE);
    vi.mocked(api.openBulkStream).mockResolvedValue(new Response(null));
    sessionStorage.clear();
  });
  afterEach(() => vi.clearAllMocks());

  it("persists the batch id to sessionStorage on start", async () => {
    const { result } = renderHook(useHarness, { wrapper });
    await act(async () => {
      await result.current.bulk.start(["CUST-1"]);
    });
    await waitFor(() => expect(result.current.bulk.status?.batch_id).toBe(7));
    expect(sessionStorage.getItem("retention.bulk.batchId")).toBe("7");
  });

  it("clears the batch (and storage) when the list query changes", async () => {
    const { result } = renderHook(useHarness, { wrapper });
    await act(async () => {
      await result.current.bulk.start(["CUST-1"]);
    });
    await waitFor(() => expect(result.current.bulk.status?.batch_id).toBe(7));

    act(() => result.current.filters.setPlan("fibre_500")); // changes customersPath(query)
    await waitFor(() => expect(result.current.bulk.status).toBeUndefined());
    expect(sessionStorage.getItem("retention.bulk.batchId")).toBeNull();
  });

  it("restores a stored batch on mount (survives navigation remount)", async () => {
    sessionStorage.setItem("retention.bulk.batchId", "7");
    const { result } = renderHook(useHarness, { wrapper });
    await waitFor(() => expect(result.current.bulk.status?.batch_id).toBe(7));
  });
});
