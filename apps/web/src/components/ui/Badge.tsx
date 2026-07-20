import { type ReactNode } from "react";

import { cn } from "@/lib/cn";

// Tone names kept stable (consumers pass gray/blue/green/amber/red); mapped to the fibre palette.
export type BadgeTone = "gray" | "blue" | "green" | "amber" | "red";

const TONES: Record<BadgeTone, string> = {
  gray: "bg-line text-ink-soft",
  blue: "bg-fibre/12 text-fibre-deep",
  green: "bg-ok/12 text-ok-deep",
  amber: "bg-signal/15 text-signal-deep",
  red: "bg-danger/12 text-danger-deep",
};

export function Badge({ tone = "gray", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        TONES[tone],
      )}
    >
      {children}
    </span>
  );
}
