import type { CategorySpend } from "@/types";
import { NON_SPENDING_CATEGORIES } from "./categoryColors";

export interface BudgetGaugeState {
  totalBudget: number;
  totalSpent: number;
  remaining: number;
  spentPct: number;
  remainingPct: number;
  isOver: boolean;
}

export function computeBudgetGauge(byCategory: CategorySpend[]): BudgetGaugeState {
  const spendingOnly = byCategory.filter(
    (c) => !NON_SPENDING_CATEGORIES.has(c.categoryName),
  );
  const totalBudget = spendingOnly.reduce((s, c) => s + (c.monthlyLimit ?? 0), 0);
  const totalSpent = spendingOnly.reduce((s, c) => s + c.amount, 0);
  const remaining = totalBudget - totalSpent;
  const spentPct = totalBudget > 0 ? Math.min(totalSpent / totalBudget, 1) * 100 : 0;
  const remainingPct = totalBudget > 0 ? Math.max(remaining / totalBudget, 0) * 100 : 0;
  const isOver = remaining < 0;

  return { totalBudget, totalSpent, remaining, spentPct, remainingPct, isOver };
}
