// Slim sticky console header. The glowing fibre dot is the brand's one-glance signature.
export function TopBar() {
  return (
    <header className="border-line bg-surface/85 sticky top-0 z-20 border-b backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-3">
        <span className="flex items-center gap-2">
          <span
            aria-hidden
            className="bg-fibre h-2 w-2 rounded-full shadow-[0_0_10px_var(--fibre)]"
          />
          <span className="font-display text-ink text-sm font-semibold tracking-tight">
            TIME <span className="text-ink-soft font-normal">Retention</span>
          </span>
        </span>
        <span className="text-ink-soft ml-auto font-mono text-xs tracking-tight">
          recontract console
        </span>
      </div>
    </header>
  );
}
