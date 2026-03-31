import type { BudgetAssignment } from "../types";

/**
 * Returns the assignment period for a given budget.
 *
 * @param budgetId    - The budget to look up.
 * @param assignments - All budget assignments.
 * @returns `{ from: "YYYY-MM", to: "YYYY-MM" | null }` where `to` is null if
 *          this budget is still active (no later assignment exists).
 */
export function getBudgetPeriod(
  budgetId: string,
  assignments: BudgetAssignment[],
): { from: string; to: string | null } | null {
  // Find all assignments for this budget, sorted ascending
  const own = assignments
    .filter((a) => a.budgetId === budgetId)
    .sort((a, b) => a.effectiveFrom.localeCompare(b.effectiveFrom));

  if (own.length === 0) return null;

  const from = own[0].effectiveFrom;

  // Find the earliest assignment for a *different* budget that comes after `from`
  const later = assignments
    .filter((a) => a.budgetId !== budgetId && a.effectiveFrom > from)
    .sort((a, b) => a.effectiveFrom.localeCompare(b.effectiveFrom));

  const to = later.length > 0 ? prevMonth(later[0].effectiveFrom) : null;

  return { from, to };
}

/** Returns the YYYY-MM of the month before the given YYYY-MM string. */
function prevMonth(yyyyMm: string): string {
  const [y, m] = yyyyMm.split("-").map(Number);
  if (m === 1) return `${y - 1}-12`;
  return `${y}-${String(m - 1).padStart(2, "0")}`;
}

/**
 * Returns the active BudgetAssignment for a given month.
 *
 * The active assignment is the one with the most recent `effectiveFrom` that
 * is less than or equal to `month`. Future-dated assignments (effectiveFrom >
 * month) are never returned.
 *
 * @param assignments - All budget assignments, in any order.
 * @param month       - The target month in YYYY-MM format.
 * @returns The effective BudgetAssignment, or null if none applies.
 */
export function getEffectiveBudget(
  assignments: BudgetAssignment[],
  month: string,
): BudgetAssignment | null {
  const eligible = assignments.filter((a) => a.effectiveFrom <= month);
  if (eligible.length === 0) return null;

  return eligible.reduce((best, curr) =>
    curr.effectiveFrom > best.effectiveFrom ? curr : best,
  );
}
