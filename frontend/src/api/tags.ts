import type { CategorySpend, Transaction } from "../types";
import { mockTransactions } from "../__tests__/fixtures";
import { useMockMode } from "../store/mockMode";

const isMock = () => useMockMode.getState().isMockMode;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TagSummary {
  tagName: string;
  totalSpend: number;
  transactionCount: number;
}

export interface TagDetailData {
  tagName: string;
  totalSpend: number;
  transactionCount: number;
  spendOverTime: { month: string; amount: number }[];
  categoryBreakdown: CategorySpend[];
  transactions: Transaction[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function buildCategoryBreakdown(transactions: Transaction[]): CategorySpend[] {
  const map = new Map<string, { amount: number; count: number }>();

  for (const tx of transactions) {
    const entry = map.get(tx.primaryCategory) ?? { amount: 0, count: 0 };
    entry.amount += Math.abs(tx.amount);
    entry.count += 1;
    map.set(tx.primaryCategory, entry);
  }

  return Array.from(map.entries())
    .map(([name, v]) => ({
      categoryId: name,
      categoryName: name,
      amount: v.amount,
      transactionCount: v.count,
      avgPerTransaction: v.amount / v.count,
      monthlyLimit: null,
      percentOfLimit: null,
      isOverBudget: false,
    }))
    .sort((a, b) => b.amount - a.amount);
}

function buildSpendOverTime(transactions: Transaction[]): { month: string; amount: number }[] {
  const monthlyTotals = new Map<string, number>();
  for (const tx of transactions) {
    const month = tx.authorizedDate.slice(0, 7);
    monthlyTotals.set(month, (monthlyTotals.get(month) ?? 0) + Math.abs(tx.amount));
  }

  const months = Array.from(monthlyTotals.keys()).sort();
  if (months.length === 0) return [];

  const [startYear, startMonth] = months[0].split("-").map(Number);
  const [endYear, endMonth] = months[months.length - 1].split("-").map(Number);

  const result: { month: string; amount: number }[] = [];
  let year = startYear;
  let month = startMonth;
  while (year < endYear || (year === endYear && month <= endMonth)) {
    const key = `${year}-${String(month).padStart(2, "0")}`;
    result.push({ month: key, amount: monthlyTotals.get(key) ?? 0 });
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return result;
}

// ─── API Functions ────────────────────────────────────────────────────────────

export async function getTagsOverview(): Promise<TagSummary[]> {
  if (isMock()) {
    const map = new Map<string, { amount: number; count: number }>();
    for (const tx of mockTransactions) {
      if (tx.exclude) continue;
      for (const tag of tx.tags ?? []) {
        const entry = map.get(tag) ?? { amount: 0, count: 0 };
        entry.amount += Math.abs(tx.amount);
        entry.count += 1;
        map.set(tag, entry);
      }
    }
    return Array.from(map.entries())
      .map(([tagName, v]) => ({ tagName, totalSpend: v.amount, transactionCount: v.count }))
      .sort((a, b) => b.totalSpend - a.totalSpend);
  }

  const res = await fetch("/api/tags");
  if (!res.ok) throw new Error("Failed to fetch tags overview");
  const json = await res.json();
  return json.data as TagSummary[];
}

export async function getTagDetail(tagName: string): Promise<TagDetailData> {
  if (isMock()) {
    const transactions = mockTransactions
      .filter((tx) => !tx.exclude && (tx.tags ?? []).includes(tagName))
      .sort((a, b) => b.authorizedDate.localeCompare(a.authorizedDate));

    if (transactions.length === 0) {
      throw Object.assign(new Error(`Unknown tag: ${tagName}`), { status: 404 });
    }

    const totalSpend = transactions.reduce((sum, t) => sum + Math.abs(t.amount), 0);

    return {
      tagName,
      totalSpend,
      transactionCount: transactions.length,
      spendOverTime: buildSpendOverTime(transactions),
      categoryBreakdown: buildCategoryBreakdown(transactions),
      transactions,
    };
  }

  const res = await fetch(`/api/tags/${encodeURIComponent(tagName)}`);
  if (res.status === 404) throw Object.assign(new Error("Unknown tag"), { status: 404 });
  if (!res.ok) throw new Error("Failed to fetch tag detail");
  const json = await res.json();
  return json.data as TagDetailData;
}
