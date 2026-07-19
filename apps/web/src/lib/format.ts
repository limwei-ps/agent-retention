// Small display formatters. Prices and usage are integers from the API; dates are ISO strings.

export const formatRM = (myr: number): string => `RM ${myr}`;

export const formatGb = (gb: number): string => `${gb.toLocaleString()} GB`;

export function formatDate(iso: string): string {
  // iso is "YYYY-MM-DD"; render as a stable, locale-independent label.
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  return `${d} ${months[Number(m) - 1] ?? m} ${y}`;
}
