// Usage history as a signal-trace waveform (the fibre motif applied to data) rather than plain bars.
export function SignalTrace({ values, className }: { values: number[]; className?: string }) {
  if (values.length === 0) return null;

  const w = 100;
  const h = 32;
  const max = Math.max(1, ...values);
  const step = values.length > 1 ? w / (values.length - 1) : w;
  const pts = values.map((v, i): [number, number] => [i * step, h - (v / max) * (h - 3) - 1.5]);
  const line = pts
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const area = `${line} L${w},${h} L0,${h} Z`;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      className={className}
      aria-hidden
      role="presentation"
    >
      <path d={area} fill="var(--fibre)" fillOpacity="0.12" />
      <path
        d={line}
        fill="none"
        stroke="var(--fibre)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
