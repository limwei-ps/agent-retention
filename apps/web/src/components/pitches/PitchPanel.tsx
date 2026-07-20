"use client";

import { useEffect, useState } from "react";

import { PitchStatusBadge } from "@/components/pitches/PitchStatusBadge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { usePitch } from "@/providers/PitchProvider";
import type { PitchRead } from "@/types/api";

export function PitchPanel({
  customerId,
  latestPitch,
}: {
  customerId: string;
  latestPitch: PitchRead | null | undefined;
}) {
  const { getPitch, generate, seed } = usePitch();
  const pitch = getPitch(customerId);
  const [copied, setCopied] = useState(false);

  // Seed from an existing ready pitch once, before the agent has generated anything this session.
  useEffect(() => {
    if (pitch.status === "not_generated") seed(customerId, latestPitch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, latestPitch]);

  const busy = pitch.status === "generating";

  async function copy() {
    await navigator.clipboard.writeText(pitch.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="border-line bg-surface flex h-full flex-col overflow-hidden rounded-xl border">
      {/* Signature: the fibre rule comes alive (light travelling down the glass) while streaming. */}
      <div
        aria-hidden
        className={cn(
          busy ? "fibre-rule" : pitch.status === "ready" ? "fibre-rule-idle" : "bg-line h-0.5",
        )}
      />

      <div className="border-line flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="font-display text-ink font-semibold">Recontract pitch</h2>
          <PitchStatusBadge status={pitch.status} />
        </div>
        <div className="flex gap-2">
          {pitch.status === "ready" && (
            <Button variant="secondary" onClick={copy}>
              {copied ? "Copied!" : "Copy"}
            </Button>
          )}
          <Button onClick={() => generate(customerId, pitch.status === "ready")} disabled={busy}>
            {busy ? "Generating…" : pitch.status === "ready" ? "Regenerate" : "Generate"}
          </Button>
        </div>
      </div>

      <div className="flex-1 p-4">
        {pitch.note && (
          <p className="text-signal-deep mb-2 flex items-center gap-2 text-xs">
            <Spinner className="text-fibre h-3 w-3" /> {pitch.note}
          </p>
        )}

        {pitch.status === "not_generated" && (
          <p className="text-ink-soft text-sm">
            No pitch yet. Click <span className="text-ink font-medium">Generate</span> to stream a
            grounded recontract pitch.
          </p>
        )}

        {pitch.status === "failed" && (
          <p className="text-danger-deep text-sm">
            Generation failed: {pitch.error ?? "unknown error"}.
          </p>
        )}

        {(pitch.status === "generating" || pitch.status === "ready") && (
          <p className="text-ink text-[15px] leading-relaxed whitespace-pre-wrap">
            {pitch.text}
            {busy && <span className="text-fibre ml-0.5 inline-block animate-pulse">▋</span>}
          </p>
        )}
      </div>

      {pitch.status === "ready" && (
        <div className="border-line text-ink-soft tnum border-t px-4 py-2.5 font-mono text-[11px]">
          {pitch.meta ? (
            <span>
              {pitch.meta.model}
              {pitch.meta.cache_hit ? " · cache hit" : ""}
              {pitch.meta.stale ? " · stale fallback" : ""} · grounded{" "}
              {pitch.meta.grounding_ok ? "✓" : "✗"} · ${pitch.meta.cost_usd.toFixed(4)} ·{" "}
              {pitch.meta.prompt_tokens + pitch.meta.completion_tokens} tok
              {pitch.meta.trace_id ? ` · trace ${pitch.meta.trace_id}` : ""}
            </span>
          ) : (
            <span>
              {pitch.model ?? "existing pitch"} · grounded {pitch.groundingOk ? "✓" : "✗"}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
