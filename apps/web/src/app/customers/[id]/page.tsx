"use client";

import Link from "next/link";
import { use } from "react";

import { PitchPanel } from "@/components/pitches/PitchPanel";
import { Spinner } from "@/components/ui/Spinner";
import { useCustomerDetail } from "@/hooks/useCustomerDetail";
import { formatDate, formatGb, formatRM } from "@/lib/format";

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading, isError } = useCustomerDetail(id);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 p-6">
      <Link href="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
        ← Back to list
      </Link>

      {isLoading && (
        <div className="flex items-center gap-2 py-8 text-sm text-gray-500">
          <Spinner /> Loading customer…
        </div>
      )}
      {(isError || (!data && !isLoading)) && (
        <p className="py-8 text-sm text-red-600">Could not load this customer.</p>
      )}

      {data && (
        <div className="grid gap-4 md:grid-cols-2">
          <section className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
            <h1 className="text-xl font-semibold">{data.name}</h1>
            <p className="text-xs text-gray-400">
              {data.id} · {data.region}
            </p>

            <dl className="mt-4 grid grid-cols-2 gap-y-2 text-sm">
              <Field label="Current plan" value={data.current_plan.name} />
              <Field label="Monthly price" value={formatRM(data.monthly_price)} />
              <Field label="Tenure" value={`${data.tenure_months} months`} />
              <Field label="Expires" value={formatDate(data.contract_end_date)} />
              <Field label="Avg usage" value={formatGb(data.avg_monthly_gb)} />
              <Field label="Last month" value={formatGb(data.last_month_gb)} />
            </dl>

            <h2 className="mt-5 mb-2 text-xs font-semibold text-gray-500 uppercase">
              Usage history
            </h2>
            <UsageHistory history={data.usage_history} />
          </section>

          <PitchPanel customerId={data.id} latestPitch={data.latest_pitch} />
        </div>
      )}
    </main>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-gray-400">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

function UsageHistory({ history }: { history: { month: string; gb: number }[] }) {
  const max = Math.max(1, ...history.map((h) => h.gb));
  return (
    <ul className="flex flex-col gap-1">
      {history.map((h) => (
        <li key={h.month} className="flex items-center gap-2 text-xs">
          <span className="w-16 shrink-0 text-gray-400 tabular-nums">{h.month}</span>
          <span className="h-2 flex-1 overflow-hidden rounded bg-gray-100 dark:bg-gray-800">
            <span
              className="block h-full bg-blue-400"
              style={{ width: `${(h.gb / max) * 100}%` }}
            />
          </span>
          <span className="w-16 shrink-0 text-right tabular-nums">{formatGb(h.gb)}</span>
        </li>
      ))}
    </ul>
  );
}
