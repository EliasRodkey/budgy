import type { MonthlySummary } from "../types";
import { mockMonthlySummaries } from "../__tests__/fixtures";

const USE_MOCK = false;

export async function getMonthlySummary(month: string): Promise<MonthlySummary> {
  if (USE_MOCK) {
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
  const res = await fetch("/api/summaries/dirty");
  if (!res.ok) throw new Error("Failed to check dirty months");
  return res.json();
}

export async function recomputeSummaries(): Promise<void> {
  const res = await fetch("/api/summaries/recompute", { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger summary recompute");
}
