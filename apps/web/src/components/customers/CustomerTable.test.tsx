import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/providers/FiltersProvider", () => ({
  useFilters: () => ({ query: {}, page: 1, pageSize: 10, setPage: vi.fn() }),
}));

const customer = {
  id: "CUST-1",
  name: "Alice Tan",
  current_plan: { id: "fibre_300", name: "TIME Fibre 300", speed_mbps: 300, price_myr: 129 },
  tenure_months: 12,
  avg_monthly_gb: 400,
  contract_end_date: "2026-07-20",
  latest_pitch_status: null,
};
vi.mock("@/hooks/useCustomers", () => ({
  useCustomers: () => ({
    data: { data: [customer], page: 1, page_size: 10, total: 1 },
    isLoading: false,
    isError: false,
    isFetching: false,
  }),
}));

import { CustomerTable } from "@/components/customers/CustomerTable";

describe("CustomerTable row select", () => {
  beforeEach(() => push.mockClear());

  it("highlights on first click, opens on the second (highlight then open)", () => {
    render(<CustomerTable />);
    const row = screen.getByRole("button", { name: /Select Alice Tan/ });

    expect(row).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(row);
    expect(row).toHaveAttribute("aria-pressed", "true"); // selected, not navigated yet
    expect(push).not.toHaveBeenCalled();

    fireEvent.click(row);
    expect(push).toHaveBeenCalledWith("/customers/CUST-1"); // second activation opens
  });

  it("keeps the name as a direct link to the detail", () => {
    render(<CustomerTable />);
    expect(screen.getByRole("link", { name: "Alice Tan" })).toHaveAttribute(
      "href",
      "/customers/CUST-1",
    );
  });
});
