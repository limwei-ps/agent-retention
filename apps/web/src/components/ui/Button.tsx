import { type ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";

const VARIANTS: Record<Variant, string> = {
  // Bright fibre with dark ink — reads as a "signal" button in both themes.
  primary: "bg-fibre text-[#04231f] hover:brightness-95 disabled:opacity-50",
  secondary:
    "border border-line bg-surface text-ink hover:border-fibre hover:text-fibre-deep disabled:opacity-50",
  ghost: "text-ink-soft hover:text-ink hover:bg-line/60",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ variant = "primary", className, ...rest }: ButtonProps) {
  return (
    <button
      className={cn(
        "focus-visible:ring-fibre focus-visible:ring-offset-surface inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium transition focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:outline-none disabled:cursor-not-allowed",
        VARIANTS[variant],
        className,
      )}
      {...rest}
    />
  );
}
