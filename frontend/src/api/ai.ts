import type { AISummary } from "../types";
import { mockAISummary } from "../__tests__/fixtures";

const USE_MOCK = true;

export async function getAISummary(month: string): Promise<AISummary> {
  if (USE_MOCK) {
    // Simulate network latency
    await new Promise((r) => setTimeout(r, 400));
    return { ...mockAISummary };
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/ai/summary", {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ month }),
  // });
  // if (!res.ok) throw new Error("Failed to generate AI summary");
  // const json = await res.json();
  // return json.data as AISummary;
  void month;
  throw new Error("Real API not implemented");
}
