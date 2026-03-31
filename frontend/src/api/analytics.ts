import type { AnalyticsSeries } from "../types";
import { mockAnalyticsSeries, mockMonthlySummaries } from "../__tests__/fixtures";

const USE_MOCK = true;

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

export interface AnalyticsData {
  series: AnalyticsSeries; // per-category spending over time
  incomeExpenses: MonthlyIncomeExpense[]; // income vs expenses per month
}

// Exposed so the Analytics page can set sensible defaults when no URL params exist
export const MOCK_DEFAULT_DATE_FROM =
  mockAnalyticsSeries.labels[0];
export const MOCK_DEFAULT_DATE_TO =
  mockAnalyticsSeries.labels[mockAnalyticsSeries.labels.length - 1];

// ─── API Function ─────────────────────────────────────────────────────────────

export async function getAnalytics(
  filters: AnalyticsFilters,
): Promise<AnalyticsData> {
  if (USE_MOCK) {
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

    return { series, incomeExpenses };
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const params = new URLSearchParams({ date_from: filters.dateFrom, date_to: filters.dateTo });
  // const res = await fetch(`/api/analytics/series?${params}`);
  // if (!res.ok) throw new Error("Failed to fetch analytics");
  // const json = await res.json();
  // return json.data as AnalyticsData;
  throw new Error("Real API not implemented");
}
