import type { MonthlySummary } from "../types";
import { mockMonthlySummaries } from "../__tests__/fixtures";
import { useMockMode } from "../store/mockMode";

const isMock = () => useMockMode.getState().isMockMode;

export async function getMonthlySummary(month: string): Promise<MonthlySummary> {
  if (isMock()) {
    const summary = mockMonthlySummaries.find((s) => s.month === month);
    if (!summary) {
      return mockMonthlySummaries[mockMonthlySummaries.length - 1];
    }
    return summary;
  }

  const res = await fetch(`/api/summaries/${month}`);
  if (!res.ok) throw new Error(`Failed to fetch summary for ${month}`);
  const json = await res.json();
  return json.data as MonthlySummary;
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
