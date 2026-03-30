import type { BudgetAssignment } from "../types";

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
