import type { CategorySpend, MonthlySummary } from "../types";
import { mockMonthlySummaries } from "../__tests__/fixtures";
import { useMockMode } from "../store/mockMode";

const isMock = () => useMockMode.getState().isMockMode;

export async function getMonthlySummary(month: string): Promise<MonthlySummary | null> {
  if (isMock()) {
    const summary = mockMonthlySummaries.find((s) => s.month === month);
    if (!summary) {
      return mockMonthlySummaries[mockMonthlySummaries.length - 1];
    }
    return summary;
  }

  const res = await fetch(`/api/summaries/${month}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to fetch summary for ${month}`);
  const json = await res.json();
  return json.data as MonthlySummary;
}

export async function getYearlySummary(year: number): Promise<MonthlySummary | null> {
  if (isMock()) {
    const yearStr = String(year);
    const rows = mockMonthlySummaries.filter((s) => s.month.startsWith(yearStr));
    if (rows.length === 0) return null;

    const totalIncome = rows.reduce((sum, r) => sum + r.totalIncome, 0);
    const totalExpenses = rows.reduce((sum, r) => sum + r.totalExpenses, 0);

    const byCategoryMap = new Map<string, CategorySpend>();
    for (const row of rows) {
      for (const cat of row.byCategory) {
        const existing = byCategoryMap.get(cat.categoryId);
        const amount = (existing?.amount ?? 0) + cat.amount;
        const transactionCount = (existing?.transactionCount ?? 0) + cat.transactionCount;
        const monthlyLimit = cat.monthlyLimit !== null ? cat.monthlyLimit * 12 : (existing?.monthlyLimit ?? null);
        byCategoryMap.set(cat.categoryId, {
          categoryId: cat.categoryId,
          categoryName: cat.categoryName,
          amount,
          transactionCount,
          avgPerTransaction: transactionCount > 0 ? amount / transactionCount : 0,
          monthlyLimit,
          percentOfLimit: null,
          isOverBudget: false,
        });
      }
    }

    const byCategory: CategorySpend[] = Array.from(byCategoryMap.values()).map((cat) => {
      const percentOfLimit = cat.monthlyLimit ? (cat.amount / cat.monthlyLimit) * 100 : null;
      return {
        ...cat,
        percentOfLimit,
        isOverBudget: percentOfLimit !== null && percentOfLimit > 100,
      };
    });

    return {
      month: yearStr,
      totalIncome,
      totalExpenses,
      net: totalIncome - totalExpenses,
      byCategory,
    };
  }

  const res = await fetch(`/api/summaries/year/${year}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to fetch yearly summary for ${year}`);
  const json = await res.json();
  return json.data as MonthlySummary;
}

export async function getPeriodSummary(month: number | null, year: number): Promise<MonthlySummary | null> {
  if (month !== null) {
    return getMonthlySummary(`${year}-${String(month).padStart(2, "0")}`);
  }
  return getYearlySummary(year);
}

export interface DirtyStatusResponse {
  dirty: boolean;
  months: { month: number; year: number }[];
}

export async function checkDirtyMonths(): Promise<DirtyStatusResponse> {
  if (isMock()) return { dirty: false, months: [] };
  const res = await fetch("/api/summaries/dirty");
  if (!res.ok) throw new Error("Failed to check dirty months");
  return res.json();
}

export async function recomputeSummaries(): Promise<void> {
  if (isMock()) return;
  const res = await fetch("/api/summaries/recompute", { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger summary recompute");
}

export async function getAvailableYears(): Promise<number[]> {
  if (isMock()) {
    const years = [...new Set(mockMonthlySummaries.map((s) => Number(s.month.slice(0, 4))))];
    return years.sort((a, b) => b - a);
  }
  const res = await fetch("/api/summaries/years");
  if (!res.ok) throw new Error("Failed to fetch available years");
  const json = await res.json();
  return json.years as number[];
}
