import type { Transaction } from "../types";
import { mockTransactions } from "../__tests__/fixtures";

const USE_MOCK = true;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TransactionFilters {
  search?: string;
  category?: string;
  dateFrom?: string; // YYYY-MM-DD
  dateTo?: string; // YYYY-MM-DD
  sortBy?: "date" | "amount";
  sortOrder?: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

export interface TransactionsPage {
  data: Transaction[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ImportResult {
  imported: number;
  failed: { row: number; reason: string }[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function applyFilters(txs: Transaction[], filters: TransactionFilters): Transaction[] {
  let result = [...txs];

  if (filters.search) {
    const q = filters.search.toLowerCase();
    result = result.filter(
      (t) =>
        t.description.toLowerCase().includes(q) ||
        t.merchant.toLowerCase().includes(q),
    );
  }

  if (filters.category) {
    result = result.filter(
      (t) =>
        t.primaryCategory === filters.category ||
        t.detailedCategory === filters.category,
    );
  }

  if (filters.dateFrom) {
    result = result.filter((t) => t.date >= filters.dateFrom!);
  }

  if (filters.dateTo) {
    result = result.filter((t) => t.date <= filters.dateTo!);
  }

  const sortBy = filters.sortBy ?? "date";
  const sortOrder = filters.sortOrder ?? "desc";

  result.sort((a, b) => {
    let cmp = 0;
    if (sortBy === "date") {
      cmp = a.date < b.date ? -1 : a.date > b.date ? 1 : 0;
    } else {
      cmp = a.amount - b.amount;
    }
    return sortOrder === "asc" ? cmp : -cmp;
  });

  return result;
}

// In-memory mutable copy for edit/delete mock operations
let mutableTransactions = [...mockTransactions];

// ─── API Functions ────────────────────────────────────────────────────────────

export async function getTransactions(filters: TransactionFilters = {}): Promise<TransactionsPage> {
  if (USE_MOCK) {
    const filtered = applyFilters(mutableTransactions, filters);
    const page = filters.page ?? 1;
    const pageSize = filters.pageSize ?? 20;
    const start = (page - 1) * pageSize;
    return {
      data: filtered.slice(start, start + pageSize),
      total: filtered.length,
      page,
      pageSize,
    };
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const params = new URLSearchParams();
  // if (filters.search) params.set("search", filters.search);
  // if (filters.category) params.set("category", filters.category);
  // if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  // if (filters.dateTo) params.set("date_to", filters.dateTo);
  // if (filters.sortBy) params.set("sort_by", filters.sortBy);
  // if (filters.sortOrder) params.set("sort_order", filters.sortOrder);
  // params.set("page", String(filters.page ?? 1));
  // params.set("page_size", String(filters.pageSize ?? 20));
  // const res = await fetch(`/api/transactions?${params}`);
  // if (!res.ok) throw new Error("Failed to fetch transactions");
  // const json = await res.json();
  // return { data: json.data, total: json.meta.total, page: json.meta.page, pageSize: json.meta.page_size };
  throw new Error("Real API not implemented");
}

export async function getFlaggedTransactions(): Promise<Transaction[]> {
  if (USE_MOCK) {
    return mutableTransactions.filter((t) => t.isFlagged);
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/transactions?flagged=true&page_size=100");
  // if (!res.ok) throw new Error("Failed to fetch flagged transactions");
  // const json = await res.json();
  // return json.data as Transaction[];
  throw new Error("Real API not implemented");
}

export async function updateTransaction(
  id: string,
  updates: Partial<Pick<Transaction, "description" | "merchant" | "amount" | "date" | "primaryCategory" | "detailedCategory" | "isFlagged" | "isExcluded" | "isRepayment">>,
): Promise<Transaction> {
  if (USE_MOCK) {
    const idx = mutableTransactions.findIndex((t) => t.id === id);
    if (idx === -1) throw new Error(`Transaction ${id} not found`);
    const updated = { ...mutableTransactions[idx], ...updates };
    mutableTransactions[idx] = updated;
    return updated;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/transactions/${id}`, {
  //   method: "PUT",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify(updates),
  // });
  // if (!res.ok) throw new Error("Failed to update transaction");
  // const json = await res.json();
  // return json.data as Transaction;
  throw new Error("Real API not implemented");
}

export async function deleteTransaction(id: string): Promise<void> {
  if (USE_MOCK) {
    const idx = mutableTransactions.findIndex((t) => t.id === id);
    if (idx === -1) throw new Error(`Transaction ${id} not found`);
    mutableTransactions.splice(idx, 1);
    return;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/transactions/${id}`, { method: "DELETE" });
  // if (!res.ok) throw new Error("Failed to delete transaction");
  throw new Error("Real API not implemented");
}

export async function assignCategory(
  transactionId: string,
  primaryCategory: string,
  detailedCategory: string,
): Promise<Transaction> {
  if (USE_MOCK) {
    return updateTransaction(transactionId, { primaryCategory, detailedCategory, isFlagged: false });
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/transactions/${transactionId}`, {
  //   method: "PUT",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ primaryCategory, detailedCategory, isFlagged: false }),
  // });
  // if (!res.ok) throw new Error("Failed to assign category");
  // const json = await res.json();
  // return json.data as Transaction;
  throw new Error("Real API not implemented");
}

export async function importTransactions(_file: File): Promise<ImportResult> {
  if (USE_MOCK) {
    // Simulate a realistic import: 5 successes, 2 failures
    await new Promise((r) => setTimeout(r, 600));
    return {
      imported: 5,
      failed: [
        { row: 3, reason: "Missing required field: date" },
        { row: 7, reason: "Invalid amount format: 'not-a-number'" },
      ],
    };
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const formData = new FormData();
  // formData.append("file", _file);
  // const res = await fetch("/api/transactions/import", { method: "POST", body: formData });
  // if (!res.ok) throw new Error("Failed to import transactions");
  // const json = await res.json();
  // return json.data as ImportResult;
  throw new Error("Real API not implemented");
}
