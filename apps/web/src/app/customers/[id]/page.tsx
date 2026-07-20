"use client";

import Link from "next/link";
import { use } from "react";

import { PitchPanel } from "@/components/pitches/PitchPanel";
import { SignalTrace } from "@/components/ui/SignalTrace";
import { Spinner } from "@/components/ui/Spinner";
import { useCustomerDetail } from "@/hooks/useCustomerDetail";
import { cn } from "@/lib/cn";
import { formatDate, formatGb, formatRM } from "@/lib/format";
import type { OfferLadder, UsagePoint } from "@/types/api";

const RUNG_LABEL: Record<string, string> = {
  retain: "Retain",
  value_upgrade: "Value upgrade",
  upsell: "Upsell",
};

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading, isError } = useCustomerDetail(id);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-6 py-8">
      <Link href="/" className="text-fibre-deep text-sm font-medium hover:underline">
        ← Back to queue
      </Link>

      {isLoading && (
        <div className="text-ink-soft flex items-center gap-2 py-8 text-sm">
          <Spinner className="text-fibre" /> Loading customer…
        </div>
      )}
      {(isError || (!data && !isLoading)) && (
        <p className="text-danger-deep py-8 text-sm">Could not load this customer.</p>
      )}

      {data && (
        <div className="grid gap-4 md:grid-cols-5">
          <section className="border-line bg-surface rounded-xl border p-5 md:col-span-2">
            <h1 className="font-display text-ink text-xl font-semibold">{data.name}</h1>
            <p className="text-ink-soft font-mono text-[11px] tracking-tight">
              {data.id} · {data.region}
            </p>

            <dl className="mt-4 grid grid-cols-2 gap-y-3 text-sm">
              <Field label="Current plan" value={data.current_plan.name} />
              <Field label="Monthly price" value={formatRM(data.monthly_price)} mono />
              <Field label="Tenure" value={`${data.tenure_months} mo`} mono />
              <Field label="Expires" value={formatDate(data.contract_end_date)} mono />
              <Field label="Avg usage" value={formatGb(data.avg_monthly_gb)} mono />
              <Field label="Last month" value={formatGb(data.last_month_gb)} mono />
            </dl>

            <Eyebrow>Usage · last 12 months</Eyebrow>
            <UsageTrace history={data.usage_history} avgGb={data.avg_monthly_gb} />

            <Eyebrow>Offer ladder</Eyebrow>
            <OfferLadderView ladder={data.offer_ladder} />
          </section>

          <div className="md:col-span-3">
            <PitchPanel customerId={data.id} latestPitch={data.latest_pitch} />
          </div>
        </div>
      )}
    </main>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-ink-soft mt-6 mb-2 font-mono text-[11px] tracking-widest uppercase">
      {children}
    </h2>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-ink-soft font-mono text-[11px] tracking-wide uppercase">{label}</dt>
      <dd className={cn("text-ink font-medium", mono && "tnum font-mono text-[13px]")}>{value}</dd>
    </div>
  );
}

function UsageTrace({ history, avgGb }: { history: UsagePoint[]; avgGb: number }) {
  return (
    <div>
      <SignalTrace values={history.map((h) => h.gb)} className="border-line h-16 w-full" />
      <div className="text-ink-soft tnum mt-1 flex justify-between font-mono text-[11px]">
        <span>{history[0]?.month}</span>
        <span>avg {formatGb(avgGb)}</span>
        <span>{history.at(-1)?.month}</span>
      </div>
    </div>
  );
}

function OfferLadderView({ ladder }: { ladder: OfferLadder }) {
  return (
    <ul className="flex flex-col gap-1.5">
      {ladder.rungs.map((rung) => {
        const recommended = rung.type === ladder.recommended;
        return (
          <li
            key={rung.type}
            className={cn(
              "rounded-lg border px-3 py-2",
              recommended ? "border-fibre/50 bg-fibre/5" : "border-line",
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-ink text-xs font-medium">
                {RUNG_LABEL[rung.type] ?? rung.type}
                {recommended && <span className="text-fibre-deep"> · recommended</span>}
              </span>
              <span className="text-ink tnum font-mono text-[12px]">
                RM {rung.monthly_price}/mo
              </span>
            </div>
            <div className="text-ink-soft mt-0.5 text-[11px]">
              {rung.target_plan.name} · {rung.term_months} mo
            </div>
          </li>
        );
      })}
    </ul>
  );
}
