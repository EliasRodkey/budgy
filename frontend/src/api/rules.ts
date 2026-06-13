import type { Rule, RuleMatchesResult } from "../types";
import { mockRules } from "../__tests__/fixtures";
import { useMockMode } from "../store/mockMode";

const isMock = () => useMockMode.getState().isMockMode;

export interface RuleInput {
  matchDescription: string;
  matchAccountName: string;
  primaryCategory?: string | null;
  detailedCategory?: string | null;
  exclude?: boolean | null;
}

// ─── Rules ────────────────────────────────────────────────────────────────────

export async function getRules(): Promise<Rule[]> {
  if (isMock()) return [...mockRules];
  const res = await fetch("/api/rules");
  if (!res.ok) throw new Error("Failed to fetch rules");
  const json = await res.json();
  return json.data as Rule[];
}

export async function createRule(payload: RuleInput): Promise<Rule> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch("/api/rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create rule");
  return (await res.json()) as Rule;
}

export async function updateRule(id: number, payload: RuleInput): Promise<Rule> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch(`/api/rules/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update rule");
  return (await res.json()) as Rule;
}

export async function deleteRule(id: number): Promise<void> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch(`/api/rules/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete rule");
}

export async function getRuleMatches(id: number): Promise<RuleMatchesResult> {
  if (isMock()) return { matchCount: 0, transactions: [] };
  const res = await fetch(`/api/rules/${id}/matches`);
  if (!res.ok) throw new Error("Failed to fetch rule matches");
  return (await res.json()) as RuleMatchesResult;
}
