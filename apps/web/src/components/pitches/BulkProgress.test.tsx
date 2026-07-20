import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { BulkProgress } from "@/components/pitches/BulkProgress";
import type { BulkBatchStatus } from "@/types/api";

const RUNNING: BulkBatchStatus = {
  batch_id: 1,
  total: 3,
  completed: 2,
  succeeded: 1,
  failed: 1,
  running: 1,
  pending: 0,
  complete: false,
  live: true,
  items: [
    { customer_id: "CUST-1", status: "succeeded", pitch_id: 10, error: null },
    { customer_id: "CUST-2", status: "failed", pitch_id: null, error: "provider down" },
    { customer_id: "CUST-3", status: "running", pitch_id: null, error: null },
  ],
};

describe("BulkProgress", () => {
  it("shows the four status buckets, friendly item labels, and a pitch link for ready items", () => {
    render(<BulkProgress status={RUNNING} />);
    const region = screen.getByRole("region", { name: /bulk generation/i });

    // Bucket labels (StatTiles) + friendly per-item badges.
    for (const label of ["Queued", "Generating", "Ready", "Failed"]) {
      expect(within(region).getAllByText(label).length).toBeGreaterThan(0);
    }
    // Raw enum strings must not leak into the UI.
    expect(within(region).queryByText("succeeded")).not.toBeInTheDocument();

    expect(within(region).getByText("provider down")).toBeInTheDocument();
    // Ready item links to its pitch.
    expect(within(region).getByRole("link", { name: /open pitch/i })).toHaveAttribute(
      "href",
      "/customers/CUST-1",
    );
  });

  it("orders items action-first (failed → running → ready) and shows N / total", () => {
    render(<BulkProgress status={RUNNING} />);
    const region = screen.getByRole("region", { name: /bulk generation/i });
    expect(within(region).getByText("2 / 3")).toBeInTheDocument();

    const ids = within(region)
      .getAllByText(/^CUST-\d$/)
      .map((el) => el.textContent);
    expect(ids).toEqual(["CUST-2", "CUST-3", "CUST-1"]); // failed, running, ready
  });

  it("reflects progress in the progressbar aria value", () => {
    render(<BulkProgress status={RUNNING} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "67");
  });

  it("offers Retry failed when the batch is complete with failures", async () => {
    const onRetryFailed = vi.fn();
    const done: BulkBatchStatus = {
      ...RUNNING,
      completed: 3,
      running: 0,
      complete: true,
      items: RUNNING.items.map((i) => (i.status === "running" ? { ...i, status: "succeeded" } : i)),
    };
    render(<BulkProgress status={done} onRetryFailed={onRetryFailed} />);

    expect(screen.getByText("Done")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /retry 1 failed/i }));
    expect(onRetryFailed).toHaveBeenCalledOnce();
  });
});
