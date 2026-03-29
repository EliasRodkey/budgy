/**
 * Format a dollar amount with sign and 2 decimal places.
 * Negative values are shown with a leading minus sign.
 */
export function formatCurrency(amount: number): string {
  const abs = Math.abs(amount);
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(abs);
  return amount < 0 ? `-${formatted}` : formatted;
}

/**
 * Format a YYYY-MM string into a human-readable month label, e.g. "March 2025".
 */
export function formatMonth(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  const date = new Date(year, mon - 1, 1);
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

/**
 * Format an ISO 8601 date string into a short locale date, e.g. "Mar 20, 2025".
 */
export function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/**
 * Return the current month as a YYYY-MM string.
 */
export function currentMonth(): string {
  const now = new Date();
  const year = now.getFullYear();
  const mon = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${mon}`;
}
