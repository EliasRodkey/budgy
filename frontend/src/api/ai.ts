import type { AISummary, NormalizationPlan } from "../types";
import { mockAISummary } from "../__tests__/fixtures";
import { useMockMode } from "../store/mockMode";
import { fetchWithRetry } from "./utils";

const PLAN_REQUIRED_FIELDS = [
  "column_map",
  "category_map",
  "amount_transform",
  "issues",
  "unmapped_required_columns",
] as const;

const isMock = () => useMockMode.getState().isMockMode;

const MOCK_PLAN: NormalizationPlan = {
  column_map: {
    "Transaction Date": "date",
    "Description": "description",
    "Category": "primary_category",
    "Amount": "amount",
    "Account Name": "account_name",
  },
  category_map: {
    "Dining Out": { primary: "Food & drink", detailed: "Restaurants & bars" },
    "Gas Station": { primary: "Transportation", detailed: "Gas & ev charging" },
    "Grocery Store": { primary: "Food & drink", detailed: "Groceries" },
  },
  amount_transform: "signed",
  debit_column: null,
  credit_column: null,
  issues: [],
  unmapped_required_columns: [],
  used_cache: false,
  requires_manual_review: false,
};

export async function getAISummary(month: string): Promise<AISummary> {
  if (isMock()) {
    await new Promise((r) => setTimeout(r, 400));
    return { ...mockAISummary };
  }

  const res = await fetchWithRetry("/api/ai/summary", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ month }),
  });

  if (!res.ok) {
    let detail = `AI summary failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch { /* ignore parse errors */ }
    throw new Error(detail);
  }

  const json = await res.json();
  return json.data as AISummary;
}

export async function planCSV(file: File): Promise<NormalizationPlan> {
  if (isMock()) {
    await new Promise((r) => setTimeout(r, 1500));
    return { ...MOCK_PLAN };
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetchWithRetry("/api/ai/plan-csv", { method: "POST", body: formData });
  if (!res.ok) {
    let detail = `Analysis failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch { /* ignore parse errors */ }
    throw new Error(detail);
  }
  const plan = await res.json();
  const missing = PLAN_REQUIRED_FIELDS.filter((f) => !(f in plan));
  if (missing.length > 0) {
    throw new Error(`Analysis returned an unexpected response (missing: ${missing.join(", ")}). Please try again.`);
  }
  return plan as NormalizationPlan;
}
