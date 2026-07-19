"use client";

import { useEffect, useState } from "react";

import { PitchStatusBadge } from "@/components/pitches/PitchStatusBadge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
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
    <div className="flex h-full flex-col rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold">Recontract pitch</h2>
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
          <p className="mb-2 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
            <Spinner className="h-3 w-3" /> {pitch.note}
          </p>
        )}

        {pitch.status === "not_generated" && (
          <p className="text-sm text-gray-500">
            No pitch yet. Click <span className="font-medium">Generate</span> to stream a grounded
            recontract pitch.
          </p>
        )}

        {pitch.status === "failed" && (
          <p className="text-sm text-red-600">
            Generation failed: {pitch.error ?? "unknown error"}.
          </p>
        )}

        {(pitch.status === "generating" || pitch.status === "ready") && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {pitch.text}
            {busy && <span className="ml-0.5 inline-block animate-pulse">▋</span>}
          </p>
        )}
      </div>

      {pitch.status === "ready" && (
        <div className="border-t border-gray-100 px-4 py-2 text-xs text-gray-500 dark:border-gray-800">
          {pitch.meta ? (
            <span className="tabular-nums">
              {pitch.meta.model}
              {pitch.meta.cache_hit ? " · cache hit" : ""}
              {pitch.meta.stale ? " · stale fallback" : ""} · grounded:{" "}
              {pitch.meta.grounding_ok ? "yes" : "no"} · ${pitch.meta.cost_usd.toFixed(4)} ·{" "}
              {pitch.meta.prompt_tokens + pitch.meta.completion_tokens} tokens
            </span>
          ) : (
            <span>
              {pitch.model ?? "existing pitch"} · grounded: {pitch.groundingOk ? "yes" : "no"}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
