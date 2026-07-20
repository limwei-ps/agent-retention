import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { FiltersProvider, useFilters } from "./FiltersProvider";

function wrapper({ children }: { children: ReactNode }) {
  return <FiltersProvider>{children}</FiltersProvider>;
}

const setup = () => renderHook(() => useFilters(), { wrapper });

describe("FiltersProvider bucket → range mapping", () => {
  it("maps a bounded tenure bucket to inclusive min/max", () => {
    const { result } = setup();
    act(() => result.current.setTenure("13-36"));
    expect(result.current.query.tenure_min).toBe(13);
    expect(result.current.query.tenure_max).toBe(36);
  });

  it("maps an open-ended bucket to a min with no max", () => {
    const { result } = setup();
    act(() => result.current.setTenure("37+"));
    expect(result.current.query.tenure_min).toBe(37);
    expect(result.current.query.tenure_max).toBeUndefined();
  });

  it("maps a usage bucket independently of tenure", () => {
    const { result } = setup();
    act(() => result.current.setUsage("500+"));
    expect(result.current.query.usage_min).toBe(500);
    expect(result.current.query.usage_max).toBeUndefined();
    expect(result.current.query.tenure_min).toBeUndefined();
  });

  it('treats "" as "any" — no range params emitted', () => {
    const { result } = setup();
    act(() => result.current.setTenure("13-36"));
    act(() => result.current.setTenure(""));
    expect(result.current.query.tenure_min).toBeUndefined();
    expect(result.current.query.tenure_max).toBeUndefined();
  });
});

describe("FiltersProvider paging", () => {
  it("resets to page 1 when a filter changes but preserves page on setPage", () => {
    const { result } = setup();
    act(() => result.current.setPage(3));
    expect(result.current.page).toBe(3);

    act(() => result.current.setPlan("fibre_500"));
    expect(result.current.page).toBe(1); // filter change resets paging
  });
});
