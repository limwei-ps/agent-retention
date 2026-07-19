import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PitchStatusBadge } from "@/components/pitches/PitchStatusBadge";

describe("PitchStatusBadge", () => {
  it("labels each known status", () => {
    const { rerender } = render(<PitchStatusBadge status="ready" />);
    expect(screen.getByText("Ready")).toBeInTheDocument();

    rerender(<PitchStatusBadge status="generating" />);
    expect(screen.getByText("Generating")).toBeInTheDocument();

    rerender(<PitchStatusBadge status="failed" />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("falls back to 'Not generated' for null/unknown", () => {
    const { rerender } = render(<PitchStatusBadge status={null} />);
    expect(screen.getByText("Not generated")).toBeInTheDocument();

    rerender(<PitchStatusBadge status="mystery" />);
    expect(screen.getByText("Not generated")).toBeInTheDocument();
  });
});
