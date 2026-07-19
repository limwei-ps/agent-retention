import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BulkProgress } from "@/components/pitches/BulkProgress";
import type { BulkBatchStatus } from "@/types/api";

const STATUS: BulkBatchStatus = {
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
  it("renders the X-of-N summary and per-item statuses", () => {
    render(<BulkProgress status={STATUS} />);

    expect(screen.getByText(/2 of 3/)).toBeInTheDocument();
    expect(screen.getByText(/1 ok · 1 failed/)).toBeInTheDocument();

    for (const id of ["CUST-1", "CUST-2", "CUST-3"]) {
      expect(screen.getByText(id)).toBeInTheDocument();
    }
    expect(screen.getByText("succeeded")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("provider down")).toBeInTheDocument();
  });

  it("reflects progress in the progressbar aria value", () => {
    render(<BulkProgress status={STATUS} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "67");
  });
});
