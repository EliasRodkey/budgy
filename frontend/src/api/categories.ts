import type { Category, CategorySpend, Transaction } from "../types";
import {
  mockCategories,
  mockMonthlySummaries,
  mockAnalyticsSeries,
  mockTransactions,
  mockBudgets,
  mockBudgetAssignments,
} from "../__tests__/fixtures";

const USE_MOCK = true;

// ─── Category mapping (hierarchy for dropdowns/filters) ──────────────────────

export interface CategoryMappingData {
  primaryCategories: string[];
  categoryMapping: Record<string, string[]>;
  excludeCategories: string[];
}

export async function fetchCategoryMapping(): Promise<CategoryMappingData> {
  const res = await fetch("/api/categories");
  if (!res.ok) throw new Error("Failed to fetch category mapping");
  return res.json();
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CategoryDetailData {
  primaryCategory: string;
  spendOverTime: { month: string; amount: number }[];
  subcategories: CategorySpend[];
  currentMonthSubcategories: CategorySpend[];
  budget: number | null;
  currentMonthTotal: number;
  currentMonthTxCount: number;
  yearAvgSpend: number;
  currentMonthTransactions: Transaction[];
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

export async function getCategoryOverview(_month: string): Promise<CategorySpend[]> {
  if (USE_MOCK) {
    // Resolve the active budget: assignment with most recent effectiveFrom <= _month
    const validAssignments = mockBudgetAssignments
      .filter((a) => a.effectiveFrom <= _month)
      .sort((a, b) => b.effectiveFrom.localeCompare(a.effectiveFrom));
    const activeBudget = validAssignments.length
      ? mockBudgets.find((b) => b.id === validAssignments[0].budgetId)
      : mockBudgets.at(-1); // fallback: most recently created

    const limits: Record<string, number> = activeBudget?.categoryLimits ?? {};

    // All 16 primary categories — always appear even with $0
    const ALL_PRIMARY_CATEGORIES = [
      "Income", "Transfers", "Debt payments", "Investments", "Bank fees",
      "Food & drink", "Shopping", "Housing & utilities", "Health & wellness",
      "Entertainment", "Insurance", "Services", "Transportation",
      "Travel", "Government & charity", "Other",
    ];

    const map = new Map<string, { amount: number; count: number; catId: string }>();

    // Pre-populate all categories at $0
    for (const name of ALL_PRIMARY_CATEGORIES) {
      map.set(name, {
        amount: 0,
        count: 0,
        catId: mockCategories.find((c) => c.level === "primary" && c.name === name)?.id ?? name,
      });
    }

    // Filter to the requested month; fall back to the latest available mock month if none match
    // (mock data uses fixed past dates and won't match the real current month)
    const monthTransactions = mockTransactions.filter(
      (tx) => !tx.exclude && tx.authorizedDate.startsWith(_month),
    );
    let txSource = monthTransactions;
    if (txSource.length === 0) {
      const latestMonth = mockTransactions
        .map((tx) => tx.authorizedDate.slice(0, 7))
        .sort()
        .at(-1) ?? "";
      txSource = mockTransactions.filter((tx) => !tx.exclude && tx.authorizedDate.startsWith(latestMonth));
    }

    for (const tx of txSource) {
      const key = tx.primaryCategory;
      const entry = map.get(key) ?? {
        amount: 0,
        count: 0,
        catId: mockCategories.find((c) => c.level === "primary" && c.name === key)?.id ?? key,
      };
      entry.amount += Math.abs(tx.amount);
      entry.count += 1;
      map.set(key, entry);
    }

    return Array.from(map.entries())
      .map(([name, v]) => {
        const limit = limits[name] ?? null;
        const pct = limit !== null ? (v.amount / limit) * 100 : null;
        return {
          categoryId: v.catId,
          categoryName: name,
          amount: v.amount,
          transactionCount: v.count,
          avgPerTransaction: v.count > 0 ? v.amount / v.count : 0,
          monthlyLimit: limit,
          percentOfLimit: pct,
          isOverBudget: pct !== null && pct > 100,
        };
      })
      .sort((a, b) => b.amount - a.amount);
  }

  // Real fetch stub
  // const res = await fetch(`/api/summary/${_month}`);
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

    // Resolve active budget for this category
    const currentMonth = new Date().toISOString().slice(0, 7);
    const validAssignments = mockBudgetAssignments
      .filter((a) => a.effectiveFrom <= currentMonth)
      .sort((a, b) => b.effectiveFrom.localeCompare(a.effectiveFrom));
    const activeBudget = validAssignments.length
      ? mockBudgets.find((b) => b.id === validAssignments[0].budgetId)
      : mockBudgets.at(-1);
    const budget: number | null = activeBudget?.categoryLimits?.[primaryCategory] ?? null;

    // Resolve current-month transactions (fall back to latest mock month if no match)
    const monthTxs = mockTransactions.filter(
      (tx) => !tx.exclude && tx.primaryCategory === primaryCategory && tx.authorizedDate.startsWith(currentMonth),
    );
    const latestMonth = mockTransactions
      .map((tx) => tx.authorizedDate.slice(0, 7))
      .sort()
      .at(-1) ?? "";
    const txSource = monthTxs.length > 0
      ? monthTxs
      : mockTransactions.filter(
          (tx) => !tx.exclude && tx.primaryCategory === primaryCategory && tx.authorizedDate.startsWith(latestMonth),
        );

    const currentMonthSubcategories = buildSubcategorySpend(txSource, primaryCategory);
    const currentMonthTotal = txSource.reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
    const currentMonthTxCount = txSource.length;
    const currentMonthTransactions = [...txSource].sort((a, b) => b.authorizedDate.localeCompare(a.authorizedDate));

    // Year average: monthly totals for the current year, fall back to latest available year
    const currentYear = currentMonth.slice(0, 4);
    const yearTxs = mockTransactions.filter(
      (tx) => !tx.exclude && tx.primaryCategory === primaryCategory && tx.authorizedDate.startsWith(currentYear),
    );
    const yearTxSource = yearTxs.length > 0 ? yearTxs : mockTransactions.filter(
      (tx) => !tx.exclude && tx.primaryCategory === primaryCategory,
    );
    const monthlyTotals = new Map<string, number>();
    for (const tx of yearTxSource) {
      const m = tx.authorizedDate.slice(0, 7);
      monthlyTotals.set(m, (monthlyTotals.get(m) ?? 0) + Math.abs(tx.amount));
    }
    const totalsArr = Array.from(monthlyTotals.values());
    const yearAvgSpend = totalsArr.length > 0
      ? totalsArr.reduce((s, v) => s + v, 0) / totalsArr.length
      : 0;

    return {
      primaryCategory,
      spendOverTime,
      subcategories,
      currentMonthSubcategories,
      budget,
      currentMonthTotal,
      currentMonthTxCount,
      yearAvgSpend,
      currentMonthTransactions,
    };
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
        !t.exclude,
    );

    const totalAmount = transactions.reduce((sum, t) => sum + Math.abs(t.amount), 0);
    const transactionCount = transactions.length;
    const avgTransactionSize = transactionCount > 0 ? totalAmount / transactionCount : 0;

    // Aggregate top vendors
    const vendorMap = new Map<string, { amount: number; count: number }>();
    for (const tx of transactions) {
      const entry = vendorMap.get(tx.accountName) ?? { amount: 0, count: 0 };
      entry.amount += Math.abs(tx.amount);
      entry.count += 1;
      vendorMap.set(tx.accountName, entry);
    }
    const topVendors = Array.from(vendorMap.entries())
      .map(([name, v]) => ({ name, amount: v.amount, count: v.count }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);

    // Sort transactions by date descending
    const sortedTransactions = [...transactions].sort((a, b) =>
      b.authorizedDate.localeCompare(a.authorizedDate),
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
