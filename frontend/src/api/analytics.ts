import type { AnalyticsSeries } from "../types";
import {
  mockAnalyticsSeries,
  mockMonthlySummaries,
  mockBudgets,
  mockBudgetAssignments,
  mockCategories,
} from "../__tests__/fixtures";
import { getEffectiveBudget } from "../lib/budget";

import { useMockMode } from "../store/mockMode";
const isMock = () => useMockMode.getState().isMockMode;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AnalyticsFilters {
  dateFrom: string; // YYYY-MM
  dateTo: string; // YYYY-MM
}

export interface MonthlyIncomeExpense {
  month: string; // YYYY-MM
  income: number;
  expenses: number;
  net: number;
}

export interface CategoryBudgetPoint {
  month: string; // YYYY-MM
  overUnder: number; // actual - limit (positive = over, negative = under)
}

export interface CategoryBudgetPerformance {
  categoryId: string;
  categoryName: string;
  monthlyLimit: number; // 0 for unbudgeted expense categories
  isIncome: boolean; // true = invert color convention (positive is good)
  data: CategoryBudgetPoint[];
  averageOverUnder: number;
}

export interface MonthlyBudgetTotal {
  month: string; // YYYY-MM
  overUnder: number; // sum of expense categories only (income excluded)
}

// NOTE: Future real endpoint:
//   GET /api/analytics/budget-performance?date_from=YYYY-MM&date_to=YYYY-MM
//   Returns: { budgetPerformance: CategoryBudgetPerformance[], monthlyBudgetTotals: MonthlyBudgetTotal[] }
//   Backend joins budget_assignments → budgets to resolve which limit was active per month.
//   overUnder = actual - limit for expenses; actual - monthlyIncomeEstimate for income.
//   Unbudgeted expense categories default to limit=0.

export interface AnalyticsData {
  series: AnalyticsSeries; // per-category spending over time
  incomeExpenses: MonthlyIncomeExpense[]; // income vs expenses per month
  budgetPerformance: CategoryBudgetPerformance[]; // per-category budget deviation over time
  monthlyBudgetTotals: MonthlyBudgetTotal[]; // total expense over/under per month
}

// Exposed so the Analytics page can set sensible defaults when no URL params exist
export const MOCK_DEFAULT_DATE_FROM = mockAnalyticsSeries.labels[0];
export const MOCK_DEFAULT_DATE_TO =
  mockAnalyticsSeries.labels[mockAnalyticsSeries.labels.length - 1];

// ─── API Function ─────────────────────────────────────────────────────────────

export async function getAnalytics(
  filters: AnalyticsFilters,
): Promise<AnalyticsData> {
  if (isMock()) {
    const { dateFrom, dateTo } = filters;

    // Filter to labels within the requested range
    const allLabels = mockAnalyticsSeries.labels;
    const filteredLabels = allLabels.filter(
      (label) => label >= dateFrom && label <= dateTo,
    );
    const labelIndices = filteredLabels.map((label) =>
      allLabels.indexOf(label),
    );

    // Build filtered datasets; drop categories with all-zero values in range
    const filteredDatasets = mockAnalyticsSeries.datasets
      .map((dataset) => ({
        ...dataset,
        values: labelIndices.map((i) => dataset.values[i] ?? 0),
      }))
      .filter((dataset) => dataset.values.some((v) => v > 0));
    // (mock path continues below — not reachable when isMock()=false)

    const series: AnalyticsSeries = {
      labels: filteredLabels,
      datasets: filteredDatasets,
    };

    // Derive income/expense per month from monthly summaries
    const incomeExpenses: MonthlyIncomeExpense[] = mockMonthlySummaries
      .filter((s) => s.month >= dateFrom && s.month <= dateTo)
      .map((s) => ({
        month: s.month,
        income: s.totalIncome,
        expenses: s.totalExpenses,
        net: s.net,
      }));

    // ── Budget performance derivation ─────────────────────────────────────────
    // For each month, resolve the active budget via assignment, then compute
    // over/under for every primary expense category + income.
    // Unbudgeted expense categories default to a $0 limit.

    const categoryDataMap = new Map<
      string,
      {
        categoryName: string;
        isIncome: boolean;
        monthlyLimit: number;
        pointsByMonth: Map<string, number>;
      }
    >();

    for (const month of filteredLabels) {
      const assignment = getEffectiveBudget(mockBudgetAssignments, month);
      const budget = assignment
        ? (mockBudgets.find((b) => b.id === assignment.budgetId) ?? null)
        : null;

      const summary = mockMonthlySummaries.find((s) => s.month === month);
      const spendingByCategory = new Map(
        (summary?.byCategory ?? []).map((c) => [c.categoryId, c.amount]),
      );

      // Income card
      if (budget) {
        const expectedIncome = budget.monthlyIncomeEstimate;
        const actualIncome = summary?.totalIncome ?? 0;
        const overUnder = actualIncome - expectedIncome;

        if (!categoryDataMap.has("cat-income")) {
          categoryDataMap.set("cat-income", {
            categoryName: "Income",
            isIncome: true,
            monthlyLimit: expectedIncome,
            pointsByMonth: new Map(),
          });
        }
        const entry = categoryDataMap.get("cat-income")!;
        entry.monthlyLimit = expectedIncome;
        entry.pointsByMonth.set(month, overUnder);
      }

      // Expense categories: union of explicit budget limits + categories with spending
      const allCategoryIds = new Set<string>([
        ...Object.keys(budget?.categoryLimits ?? {}).flatMap((name) => {
          const cat = mockCategories.find(
            (c) => c.name === name && c.level === "primary",
          );
          return cat ? [cat.id] : [];
        }),
        ...(summary?.byCategory.map((c) => c.categoryId) ?? []),
      ]);
      allCategoryIds.delete("cat-income");

      for (const categoryId of allCategoryIds) {
        const cat = mockCategories.find((c) => c.id === categoryId);
        if (!cat || cat.level !== "primary") continue;

        const limit = budget?.categoryLimits[cat.name] ?? 0;
        const actual = spendingByCategory.get(categoryId) ?? 0;
        const overUnder = actual - limit;

        if (!categoryDataMap.has(categoryId)) {
          categoryDataMap.set(categoryId, {
            categoryName: cat.name,
            isIncome: false,
            monthlyLimit: limit,
            pointsByMonth: new Map(),
          });
        }
        const entry = categoryDataMap.get(categoryId)!;
        entry.monthlyLimit = limit;
        entry.pointsByMonth.set(month, overUnder);
      }
    }

    // Build CategoryBudgetPerformance[]; fill missing months with (0 - limit)
    const budgetPerformance: CategoryBudgetPerformance[] = [];
    for (const [categoryId, entry] of categoryDataMap) {
      const data: CategoryBudgetPoint[] = filteredLabels.map((month) => ({
        month,
        overUnder:
          entry.pointsByMonth.get(month) ??
          (entry.isIncome ? 0 : 0 - entry.monthlyLimit),
      }));
      const averageOverUnder =
        data.reduce((sum, d) => sum + d.overUnder, 0) / (data.length || 1);
      budgetPerformance.push({
        categoryId,
        categoryName: entry.categoryName,
        monthlyLimit: entry.monthlyLimit,
        isIncome: entry.isIncome,
        data,
        averageOverUnder,
      });
    }

    // Sort: worst expense performers first (highest averageOverUnder), income last
    budgetPerformance.sort((a, b) => {
      if (a.isIncome !== b.isIncome) return a.isIncome ? 1 : -1;
      return b.averageOverUnder - a.averageOverUnder;
    });

    // Total over/under per month: expense categories only
    const expensePerformance = budgetPerformance.filter((c) => !c.isIncome);
    const monthlyBudgetTotals: MonthlyBudgetTotal[] = filteredLabels.map(
      (month) => ({
        month,
        overUnder: expensePerformance.reduce(
          (sum, cat) =>
            sum + (cat.data.find((d) => d.month === month)?.overUnder ?? 0),
          0,
        ),
      }),
    );

    return { series, incomeExpenses, budgetPerformance, monthlyBudgetTotals };
  }

  const params = new URLSearchParams({ date_from: filters.dateFrom, date_to: filters.dateTo });
  const res = await fetch(`/api/analytics/series?${params}`);
  if (!res.ok) throw new Error("Failed to fetch analytics");
  const json = await res.json();
  return json.data as AnalyticsData;
}
