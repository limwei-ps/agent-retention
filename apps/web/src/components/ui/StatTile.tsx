import { cn } from "@/lib/cn";

// A single KPI/count tile in the "Fibre Signal" language: a big display number, a short accent rule,
// and an uppercase-mono label. Interactive when `onClick` is given (dashboard filters); otherwise a
// static readout (bulk-progress buckets). The accent rule carries the tone.
export type StatTileTone = "fibre" | "ok" | "danger" | "neutral";

const RULE: Record<StatTileTone, string> = {
  fibre: "bg-fibre",
  ok: "bg-ok",
  danger: "bg-danger",
  neutral: "bg-line",
};

interface StatTileProps {
  label: string;
  value: number | string;
  tone?: StatTileTone;
  hero?: boolean;
  active?: boolean;
  onClick?: () => void;
}

export function StatTile({ label, value, tone = "neutral", hero, active, onClick }: StatTileProps) {
  const interactive = typeof onClick === "function";
  const cls = cn(
    "min-w-28 flex-1 rounded-xl border px-4 py-3 text-left transition",
    active
      ? "border-fibre bg-fibre/8 ring-fibre/40 ring-1"
      : interactive
        ? "border-line bg-surface hover:border-fibre/50"
        : "border-line bg-surface",
    interactive && "focus-visible:ring-fibre focus-visible:ring-2 focus-visible:outline-none",
  );

  const body = (
    <>
      <div
        className={cn("font-display text-ink tnum font-semibold", hero ? "text-3xl" : "text-2xl")}
      >
        {value}
      </div>
      <div className={cn("mt-1 h-0.5 w-6 rounded", active || hero ? "bg-fibre" : RULE[tone])} />
      <div className="text-ink-soft mt-2 truncate font-mono text-[11px] tracking-wide uppercase">
        {label}
      </div>
    </>
  );

  return interactive ? (
    <button type="button" onClick={onClick} aria-pressed={active} className={cls}>
      {body}
    </button>
  ) : (
    <div className={cls}>{body}</div>
  );
}
