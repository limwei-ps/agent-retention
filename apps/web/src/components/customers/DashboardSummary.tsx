"use client";

import { Spinner } from "@/components/ui/Spinner";
import { useDashboard } from "@/hooks/useDashboard";

export function DashboardSummary() {
  const { data, isLoading, isError } = useDashboard();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Spinner /> Loading summary…
      </div>
    );
  }
  if (isError || !data) {
    return <p className="text-sm text-red-600">Could not load the dashboard summary.</p>;
  }

  return (
    <section>
      <h2 className="mb-2 text-sm font-semibold text-gray-500 uppercase">Expiring this month</h2>
      <div className="flex flex-wrap gap-3">
        <SummaryCard label="Total" value={data.expiring_this_month} highlight />
        {data.by_tier.map((tier) => (
          <SummaryCard key={tier.plan.id} label={tier.plan.name} value={tier.count} />
        ))}
      </div>
    </section>
  );
}

function SummaryCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div
      className={
        highlight
          ? "rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 dark:border-blue-800 dark:bg-blue-950"
          : "rounded-lg border border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900"
      }
    >
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}
