import type { Category, CategorySpend, Transaction } from "../types";
import {
  mockCategories,
  mockMonthlySummaries,
  mockAnalyticsSeries,
  mockTransactions,
} from "../__tests__/fixtures";

const USE_MOCK = true;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CategoryDetailData {
  primaryCategory: string;
  spendOverTime: { month: string; amount: number }[];
  subcategories: CategorySpend[];
}

export interface SubcategoryDetailData {
  primaryCategory: string;
  detailedCategory: string;
  transactionCount: number;
  avgTransactionSize: number;
  topVendors: { name: string; amount: number; count: number }[];
  transactions: Transaction[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function buildSubcategorySpend(
  transactions: Transaction[],
  primaryCategory: string,
): CategorySpend[] {
  const map = new Map<string, { amount: number; count: number; catId: string }>();

  for (const tx of transactions) {
    if (tx.primaryCategory !== primaryCategory) continue;
    const key = tx.detailedCategory;
    const entry = map.get(key) ?? { amount: 0, count: 0, catId: "" };
    // Find matching category id
    const cat = mockCategories.find(
      (c) => c.level === "detailed" && c.name === key,
    );
    entry.catId = cat?.id ?? key;
    entry.amount += Math.abs(tx.amount);
    entry.count += 1;
    map.set(key, entry);
  }

  return Array.from(map.entries())
    .filter(([, v]) => v.count > 0)
    .map(([name, v]) => ({
      categoryId: v.catId,
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

// ─── API Functions ────────────────────────────────────────────────────────────

export async function getCategories(): Promise<Category[]> {
  if (USE_MOCK) {
    return mockCategories;
  }

  // Real fetch stub
  // const res = await fetch("/api/categories");
  // if (!res.ok) throw new Error("Failed to fetch categories");
  // const json = await res.json();
  // return json.data as Category[];
  throw new Error("Real API not implemented");
}

export async function getCategoryOverview(month: string): Promise<CategorySpend[]> {
  if (USE_MOCK) {
    const summary = mockMonthlySummaries.find((s) => s.month === month);
    if (!summary) {
      // Fall back to most recent month
      const latest = mockMonthlySummaries.at(-1);
      return latest?.byCategory.filter((c) => c.transactionCount > 0) ?? [];
    }
    return summary.byCategory.filter((c) => c.transactionCount > 0);
  }

  // Real fetch stub
  // const res = await fetch(`/api/summary/${month}`);
  // if (!res.ok) throw new Error("Failed to fetch category overview");
  // const json = await res.json();
  // return (json.data as MonthlySummary).byCategory.filter((c) => c.transactionCount > 0);
  throw new Error("Real API not implemented");
}

export async function getCategoryDetail(primaryCategory: string): Promise<CategoryDetailData> {
  if (USE_MOCK) {
    const dataset = mockAnalyticsSeries.datasets.find(
      (d) => d.categoryName === primaryCategory,
    );

    const spendOverTime = dataset
      ? mockAnalyticsSeries.labels.map((month, i) => ({
          month,
          amount: dataset.values[i] ?? 0,
        }))
      : [];

    const subcategories = buildSubcategorySpend(mockTransactions, primaryCategory);

    return { primaryCategory, spendOverTime, subcategories };
  }

  // Real fetch stub
  // const res = await fetch(`/api/categories/${encodeURIComponent(primaryCategory)}`);
  // if (!res.ok) throw new Error("Failed to fetch category detail");
  // const json = await res.json();
  // return json.data as CategoryDetailData;
  throw new Error("Real API not implemented");
}

export async function getSubcategoryDetail(
  primaryCategory: string,
  detailedCategory: string,
): Promise<SubcategoryDetailData> {
  if (USE_MOCK) {
    const transactions = mockTransactions.filter(
      (t) =>
        t.primaryCategory === primaryCategory &&
        t.detailedCategory === detailedCategory &&
        !t.isExcluded,
    );

    const totalAmount = transactions.reduce((sum, t) => sum + Math.abs(t.amount), 0);
    const transactionCount = transactions.length;
    const avgTransactionSize = transactionCount > 0 ? totalAmount / transactionCount : 0;

    // Aggregate top vendors
    const vendorMap = new Map<string, { amount: number; count: number }>();
    for (const tx of transactions) {
      const entry = vendorMap.get(tx.merchant) ?? { amount: 0, count: 0 };
      entry.amount += Math.abs(tx.amount);
      entry.count += 1;
      vendorMap.set(tx.merchant, entry);
    }
    const topVendors = Array.from(vendorMap.entries())
      .map(([name, v]) => ({ name, amount: v.amount, count: v.count }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);

    // Sort transactions by date descending
    const sortedTransactions = [...transactions].sort((a, b) =>
      b.date.localeCompare(a.date),
    );

    return {
      primaryCategory,
      detailedCategory,
      transactionCount,
      avgTransactionSize,
      topVendors,
      transactions: sortedTransactions,
    };
  }

  // Real fetch stub
  // const res = await fetch(
  //   `/api/categories/${encodeURIComponent(primaryCategory)}/${encodeURIComponent(detailedCategory)}`
  // );
  // if (!res.ok) throw new Error("Failed to fetch subcategory detail");
  // const json = await res.json();
  // return json.data as SubcategoryDetailData;
  throw new Error("Real API not implemented");
}
