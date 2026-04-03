import { describe, expect, it } from "vitest";
import { computeBudgetGauge } from "../lib/budgetGauge";
import type { CategorySpend } from "../types";

const baseCategory = (
  id: string,
  amount: number,
  monthlyLimit: number | null
): CategorySpend => ({
  categoryId: id,
  categoryName: id,
  amount,
  transactionCount: 1,
  avgPerTransaction: amount,
  monthlyLimit,
  percentOfLimit: monthlyLimit ? (amount / monthlyLimit) * 100 : null,
  isOverBudget: monthlyLimit !== null && amount > monthlyLimit,
});

describe("computeBudgetGauge — under budget", () => {
  const categories: CategorySpend[] = [
    baseCategory("food", 241.04, 400),
    baseCategory("housing", 1594.0, 1800),
    baseCategory("entertainment", 15.49, 80),
    baseCategory("transfers", 150.0, null), // no limit — excluded
  ];

  it("sums only categories with limits", () => {
    const { totalBudget } = computeBudgetGauge(categories);
    expect(totalBudget).toBeCloseTo(2280); // 400 + 1800 + 80
  });

  it("computes remaining as budget minus spend", () => {
    const { remaining } = computeBudgetGauge(categories);
    expect(remaining).toBeCloseTo(2280 - (241.04 + 1594.0 + 15.49));
  });

  it("is not over budget", () => {
    const { isOver } = computeBudgetGauge(categories);
    expect(isOver).toBe(false);
  });

  it("spent bar fills less than 100%", () => {
    const { spentPct } = computeBudgetGauge(categories);
    expect(spentPct).toBeGreaterThan(0);
    expect(spentPct).toBeLessThan(100);
  });

  it("remaining bar is greater than 0%", () => {
    const { remainingPct } = computeBudgetGauge(categories);
    expect(remainingPct).toBeGreaterThan(0);
  });
});

describe("computeBudgetGauge — over budget", () => {
  // Total budget: $100 + $200 + $80 = $380
  // Total spent:  $241 + $300 + $100 = $641  → over by $261
  const categories: CategorySpend[] = [
    baseCategory("food", 241.04, 100),
    baseCategory("housing", 300.0, 200),
    baseCategory("entertainment", 100.0, 80),
  ];

  it("is over budget", () => {
    const { isOver } = computeBudgetGauge(categories);
    expect(isOver).toBe(true);
  });

  it("remaining is negative", () => {
    const { remaining } = computeBudgetGauge(categories);
    expect(remaining).toBeLessThan(0);
  });

  it("spent bar is capped at 100%", () => {
    const { spentPct } = computeBudgetGauge(categories);
    expect(spentPct).toBe(100);
  });

  it("remaining bar is clamped to 0%", () => {
    const { remainingPct } = computeBudgetGauge(categories);
    expect(remainingPct).toBe(0);
  });
});

describe("computeBudgetGauge — no limits set", () => {
  const categories: CategorySpend[] = [
    baseCategory("transfers", 150.0, null),
    baseCategory("investments", 500.0, null),
  ];

  it("totalBudget is 0", () => {
    const { totalBudget } = computeBudgetGauge(categories);
    expect(totalBudget).toBe(0);
  });

  it("bars are 0%", () => {
    const { spentPct, remainingPct } = computeBudgetGauge(categories);
    expect(spentPct).toBe(0);
    expect(remainingPct).toBe(0);
  });

  it("is not flagged as over budget", () => {
    const { isOver } = computeBudgetGauge(categories);
    expect(isOver).toBe(false);
  });
});
