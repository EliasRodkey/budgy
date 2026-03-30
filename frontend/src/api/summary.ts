import type { MonthlySummary } from "../types";
import { mockMonthlySummaries } from "../__tests__/fixtures";

const USE_MOCK = true;

export async function getMonthlySummary(month: string): Promise<MonthlySummary> {
  if (USE_MOCK) {
    const summary = mockMonthlySummaries.find((s) => s.month === month);
    if (!summary) {
      // Fall back to the latest available month
      return mockMonthlySummaries[mockMonthlySummaries.length - 1];
    }
    return summary;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/summary/${month}`);
  // if (!res.ok) throw new Error(`Failed to fetch summary for ${month}`);
  // const json = await res.json();
  // return json.data as MonthlySummary;
  throw new Error("Real API not implemented");
}
