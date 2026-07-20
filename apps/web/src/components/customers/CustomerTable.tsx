"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { PitchStatusBadge } from "@/components/pitches/PitchStatusBadge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useCustomers } from "@/hooks/useCustomers";
import { cn } from "@/lib/cn";
import { formatDate, formatGb } from "@/lib/format";
import { useFilters } from "@/providers/FiltersProvider";

export function CustomerTable() {
  const { query, page, pageSize, setPage } = useFilters();
  const { data, isLoading, isError, isFetching } = useCustomers(query);
  const router = useRouter();
  // Highlight-then-open: first click on a row selects it; a second, deliberate action opens the detail.
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const open = (id: string) => router.push(`/customers/${id}`);
  const activate = (id: string) => (id === selectedId ? open(id) : setSelectedId(id));

  if (isLoading) {
    return (
      <div className="text-ink-soft flex items-center gap-2 py-8 text-sm">
        <Spinner className="text-fibre" /> Loading customers…
      </div>
    );
  }
  if (isError || !data) {
    return <p className="text-danger-deep py-8 text-sm">Could not load customers.</p>;
  }

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));
  const th = "px-3 py-2.5 font-medium";
  const td = "px-3 py-2.5";
  const dataCell = `${td} font-mono text-[13px] text-ink tnum`;

  return (
    <div className={isFetching ? "opacity-60 transition-opacity" : undefined}>
      <div className="border-line bg-surface overflow-x-auto rounded-xl border">
        <table className="w-full text-left text-sm">
          <thead className="border-line text-ink-soft border-b font-mono text-[11px] tracking-wide uppercase">
            <tr>
              <th className={th}>Customer</th>
              <th className={th}>Plan</th>
              <th className={th}>Tenure</th>
              <th className={th}>Avg usage</th>
              <th className={th}>Expires</th>
              <th className={th}>Pitch</th>
            </tr>
          </thead>
          <tbody className="divide-line divide-y">
            {data.data.map((c) => {
              const isSelected = c.id === selectedId;
              return (
                <tr
                  key={c.id}
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSelected}
                  aria-label={`Select ${c.name}; activate again to open`}
                  onClick={() => activate(c.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      activate(c.id);
                    }
                  }}
                  className={cn(
                    "hover:bg-paper cursor-pointer transition-colors",
                    isSelected && "bg-fibre/8 ring-fibre/40 ring-1 ring-inset",
                  )}
                >
                  <td className={td}>
                    <Link
                      href={`/customers/${c.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-fibre-deep font-medium hover:underline"
                    >
                      {c.name}
                    </Link>
                    <div className="text-ink-soft font-mono text-[11px]">{c.id}</div>
                  </td>
                  <td className={`${td} text-ink`}>{c.current_plan.name}</td>
                  <td className={dataCell}>{c.tenure_months} mo</td>
                  <td className={dataCell}>{formatGb(c.avg_monthly_gb)}</td>
                  <td className={dataCell}>{formatDate(c.contract_end_date)}</td>
                  <td className={td}>
                    <div className="flex items-center justify-between gap-2">
                      <PitchStatusBadge status={c.latest_pitch_status} />
                      {isSelected && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            open(c.id);
                          }}
                          className="text-fibre-deep text-xs font-medium hover:underline"
                        >
                          Open →
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {data.data.length === 0 && (
              <tr>
                <td colSpan={6} className="text-ink-soft px-3 py-10 text-center">
                  No customers match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-ink-soft mt-3 flex items-center justify-between text-sm">
        <span className="tnum font-mono text-[13px]">
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
