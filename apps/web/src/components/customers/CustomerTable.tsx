"use client";

import Link from "next/link";

import { PitchStatusBadge } from "@/components/pitches/PitchStatusBadge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useCustomers } from "@/hooks/useCustomers";
import { formatDate, formatGb } from "@/lib/format";
import { useFilters } from "@/providers/FiltersProvider";

export function CustomerTable() {
  const { query, page, pageSize, setPage } = useFilters();
  const { data, isLoading, isError, isFetching } = useCustomers(query);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-8 text-sm text-gray-500">
        <Spinner /> Loading customers…
      </div>
    );
  }
  if (isError || !data) {
    return <p className="py-8 text-sm text-red-600">Could not load customers.</p>;
  }

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));

  return (
    <div className={isFetching ? "opacity-60 transition-opacity" : undefined}>
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase dark:bg-gray-800">
            <tr>
              <th className="px-3 py-2 font-medium">Customer</th>
              <th className="px-3 py-2 font-medium">Plan</th>
              <th className="px-3 py-2 font-medium">Tenure</th>
              <th className="px-3 py-2 font-medium">Avg usage</th>
              <th className="px-3 py-2 font-medium">Expires</th>
              <th className="px-3 py-2 font-medium">Pitch</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {data.data.map((c) => (
              <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-3 py-2">
                  <Link
                    href={`/customers/${c.id}`}
                    className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {c.name}
                  </Link>
                  <div className="text-xs text-gray-400">{c.id}</div>
                </td>
                <td className="px-3 py-2">{c.current_plan.name}</td>
                <td className="px-3 py-2 tabular-nums">{c.tenure_months} mo</td>
                <td className="px-3 py-2 tabular-nums">{formatGb(c.avg_monthly_gb)}</td>
                <td className="px-3 py-2 tabular-nums">{formatDate(c.contract_end_date)}</td>
                <td className="px-3 py-2">
                  <PitchStatusBadge status={c.latest_pitch_status} />
                </td>
              </tr>
            ))}
            {data.data.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-gray-500">
                  No customers match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
        <span className="tabular-nums">
          {data.total} customers · page {page} of {totalPages}
        </span>
        <div className="flex gap-2">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <Button
            variant="secondary"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
