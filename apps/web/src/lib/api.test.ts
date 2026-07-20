import { describe, expect, it } from "vitest";

import { customersPath } from "./api";

describe("customersPath", () => {
  it("returns the bare path when the query is empty", () => {
    expect(customersPath({})).toBe("/api/customers");
  });

  it("serializes tenure and usage range filters", () => {
    const path = customersPath({ tenure_min: 13, tenure_max: 36, usage_min: 200, usage_max: 499 });
    const qs = new URLSearchParams(path.split("?")[1]);
    expect(qs.get("tenure_min")).toBe("13");
    expect(qs.get("tenure_max")).toBe("36");
    expect(qs.get("usage_min")).toBe("200");
    expect(qs.get("usage_max")).toBe("499");
  });

  it("serializes a 0 lower bound (0 is a meaningful value, not 'unset')", () => {
    const qs = new URLSearchParams(customersPath({ tenure_min: 0 }).split("?")[1]);
    expect(qs.get("tenure_min")).toBe("0");
  });

  it("omits range params that are undefined", () => {
    const qs = new URLSearchParams(customersPath({ tenure_min: 37 }).split("?")[1]);
    expect(qs.get("tenure_min")).toBe("37");
    expect(qs.has("tenure_max")).toBe(false);
    expect(qs.has("usage_min")).toBe(false);
  });
});
