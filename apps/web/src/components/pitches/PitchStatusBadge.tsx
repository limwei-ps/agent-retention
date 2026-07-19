import { Badge, type BadgeTone } from "@/components/ui/Badge";
import type { PitchStatus } from "@/types/api";

const STATUS: Record<PitchStatus, { tone: BadgeTone; label: string }> = {
  not_generated: { tone: "gray", label: "Not generated" },
  generating: { tone: "blue", label: "Generating" },
  ready: { tone: "green", label: "Ready" },
  failed: { tone: "red", label: "Failed" },
};

// Accept a loose string: the list endpoint types latest_pitch_status as `string | null`. Unknown or
// absent values fall back to "not generated".
export function PitchStatusBadge({ status }: { status: string | null | undefined }) {
  const entry = STATUS[(status as PitchStatus) ?? "not_generated"] ?? STATUS.not_generated;
  return <Badge tone={entry.tone}>{entry.label}</Badge>;
}
