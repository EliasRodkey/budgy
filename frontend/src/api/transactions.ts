import type { Transaction } from "../types";
import { useMockMode } from "../store/mockMode";

const isMock = () => useMockMode.getState().isMockMode;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TransactionFilters {
  search?: string;
  primaryCategory?: string;
  detailedCategory?: string;
  tags?: string[];        // OR logic: match any of these tags
  showExcluded?: boolean; // default false — excluded transactions are hidden
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
  hasNextPage: boolean;
}

export interface ImportResult {
  imported: number;
  failed: { row: number; reason: string }[];
  jobFailed: boolean;
}

export interface UploadJobResponse {
  jobId: string;
  status: string;
}

export interface ImportJobStatus {
  jobId: string;
  status: "pending" | "processing" | "complete" | "failed";
  rowsImported?: number;
  rowsUpdated?: number;
  errors?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function parseTags(tags: unknown): string[] {
  if (!tags) return [];
  if (Array.isArray(tags)) return tags as string[];
  return String(tags).split(",").map((s) => s.trim()).filter(Boolean);
}

function normalizeTransaction(tx: Record<string, unknown>): Transaction {
  return { ...tx, tags: parseTags(tx.tags) } as Transaction;
}

function applyFilters(txs: Transaction[], filters: TransactionFilters): Transaction[] {
  let result = [...txs];

  // Hide excluded transactions by default
  if (!filters.showExcluded) {
    result = result.filter((t) => !t.exclude);
  }

  if (filters.search) {
    const q = filters.search.toLowerCase();
    result = result.filter(
      (t) =>
        t.description.toLowerCase().includes(q) ||
        t.accountName.toLowerCase().includes(q),
    );
  }

  if (filters.primaryCategory) {
    result = result.filter((t) => t.primaryCategory === filters.primaryCategory);
  }

  if (filters.detailedCategory) {
    result = result.filter((t) => t.detailedCategory === filters.detailedCategory);
  }

  if (filters.tags && filters.tags.length > 0) {
    result = result.filter(
      (t) => t.tags && filters.tags!.some((tag) => t.tags!.includes(tag)),
    );
  }

  if (filters.dateFrom) {
    result = result.filter((t) => t.authorizedDate >= filters.dateFrom!);
  }

  if (filters.dateTo) {
    result = result.filter((t) => t.authorizedDate <= filters.dateTo!);
  }

  const sortBy = filters.sortBy ?? "date";
  const sortOrder = filters.sortOrder ?? "desc";

  result.sort((a, b) => {
    let cmp = 0;
    if (sortBy === "date") {
      cmp = a.authorizedDate < b.authorizedDate ? -1 : a.authorizedDate > b.authorizedDate ? 1 : 0;
    } else {
      cmp = a.amount - b.amount;
    }
    return sortOrder === "asc" ? cmp : -cmp;
  });

  return result;
}

// In-memory mutable copy for edit/delete mock operations
import { mockTransactions } from "../__tests__/fixtures";
let mutableTransactions = [...mockTransactions];

// ─── API Functions ────────────────────────────────────────────────────────────

export async function getTransactions(filters: TransactionFilters = {}): Promise<TransactionsPage> {
  if (isMock()) {
    const filtered = applyFilters(mutableTransactions, filters);
    const page = filters.page ?? 1;
    const pageSize = filters.pageSize ?? 20;
    const start = (page - 1) * pageSize;
    const hasNextPage = true;
    return {
      data: filtered.slice(start, start + pageSize),
      total: filtered.length,
      page,
      pageSize,
      hasNextPage
    };
  }

  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.primaryCategory) params.set("primaryCategory", filters.primaryCategory);
  if (filters.detailedCategory) params.set("detailedCategory", filters.detailedCategory);
  if (filters.tags?.length) params.set("tags", filters.tags.join(","));
  if (filters.showExcluded) params.set("showExcluded", "true");
  if (filters.dateFrom) params.set("dateFrom", filters.dateFrom);
  if (filters.dateTo) params.set("dateTo", filters.dateTo);
  if (filters.sortBy) params.set("sortBy", filters.sortBy);
  if (filters.sortOrder) params.set("sortOrder", filters.sortOrder);
  params.set("page", String(filters.page ?? 1));
  params.set("pageSize", String(filters.pageSize ?? 20));
  const res = await fetch(`/api/transactions?${params}`);
  if (!res.ok) throw new Error("Failed to fetch transactions");
  const json = await res.json();
  return {
    data: (json.data as Record<string, unknown>[]).map(normalizeTransaction),
    total: json.total,
    page: json.page,
    pageSize: json.pageSize,
    hasNextPage: json.hasNextPage,
  };
}

export async function getFlaggedTransactions(): Promise<Transaction[]> {
  if (isMock()) {
    return mutableTransactions.filter((t) => t.status === "Unchecked");
  }

  const res = await fetch("/api/transactions?flagged=true&page_size=100");
  if (!res.ok) throw new Error("Failed to fetch flagged transactions");
  const json = await res.json();
  return (json.data as Record<string, unknown>[]).map(normalizeTransaction);
}

export async function getAvailableTags(): Promise<string[]> {
  if (isMock()) {
    const tagSet = new Set<string>();
    for (const t of mutableTransactions) {
      if (t.tags) {
        for (const tag of t.tags) tagSet.add(tag);
      }
    }
    return [...tagSet].sort();
  }

  const res = await fetch("/api/transactions/tags");
  if (!res.ok) throw new Error("Failed to fetch tags");
  const json = await res.json();
  return json as string[];
}

export async function updateTransaction(
  id: string,
  updates: Partial<Pick<Transaction, "authorizedDate" | "postedDate" | "status" | "accountName" | "description" | "primaryCategory" | "detailedCategory" | "amount" | "repayment" | "exclude" | "notes" | "tags">>,
): Promise<Transaction> {
  if (isMock()) {
    const idx = mutableTransactions.findIndex((t) => t.id === id);
    if (idx === -1) throw new Error(`Transaction ${id} not found`);
    const updated = { ...mutableTransactions[idx], ...updates };
    mutableTransactions[idx] = updated;
    return updated;
  }

  const res = await fetch(`/api/transactions/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update transaction");
  return res.json().then(normalizeTransaction);
}

export async function deleteTransaction(id: string): Promise<void> {
  if (isMock()) {
    const idx = mutableTransactions.findIndex((t) => t.id === id);
    if (idx === -1) throw new Error(`Transaction ${id} not found`);
    mutableTransactions.splice(idx, 1);
    return;
  }

  const res = await fetch(`/api/transactions/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete transaction");
}

export async function assignCategory(
  transactionId: string,
  primaryCategory: string,
  detailedCategory: string,
): Promise<Transaction> {
  if (isMock()) {
    return updateTransaction(transactionId, { primaryCategory, detailedCategory, status });
  }

  const res = await fetch(`/api/transactions/${transactionId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ primaryCategory, detailedCategory }),
  });
  if (!res.ok) throw new Error("Failed to assign category");
  const json = await res.json();
  return json.data as Transaction;
}

export interface BulkUpdatePayload {
  transactionIds: number[];
  primaryCategory?: string;
  detailedCategory?: string;
  tags?: string[];
  exclude?: boolean;
  saveAsRule?: boolean;
  matchDescription?: string;
  matchAccountName?: string;
}

export async function getSimilarTransactions(
  description: string,
  accountName: string,
  excludeId?: number,
): Promise<Transaction[]> {
  if (isMock()) return [];
  const params = new URLSearchParams({ description, account_name: accountName });
  if (excludeId !== undefined) params.set("exclude_id", String(excludeId));
  const res = await fetch(`/api/transactions/similar?${params}`);
  if (!res.ok) throw new Error("Failed to fetch similar transactions");
  const data = await res.json() as Record<string, unknown>[];
  return data.map(normalizeTransaction);
}

export async function bulkUpdateTransactions(payload: BulkUpdatePayload): Promise<{ updated: number }> {
  if (isMock()) return { updated: payload.transactionIds.length };
  const res = await fetch("/api/transactions/bulk-update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      transaction_ids: payload.transactionIds,
      primary_category: payload.primaryCategory,
      detailed_category: payload.detailedCategory,
      tags: payload.tags,
      exclude: payload.exclude,
      save_as_rule: payload.saveAsRule ?? false,
      match_description: payload.matchDescription,
      match_account_name: payload.matchAccountName,
    }),
  });
  if (!res.ok) throw new Error("Failed to bulk update transactions");
  return res.json() as Promise<{ updated: number }>;
}

// ─── CSV Import Helpers ───────────────────────────────────────────────────────

/** Polls a job until complete/failed, then confirms and maps to ImportResult. */
export async function pollJobUntilDone(
  jobId: string,
  maxAttempts = 40,
  intervalMs = 1500,
): Promise<ImportResult> {
  for (let i = 0; i < maxAttempts; i++) {
    const status = await getImportJobStatus(jobId);
    if (status.status === "complete" || status.status === "failed") {
      await confirmImport(jobId);
      if (status.status === "failed") {
        return { imported: 0, failed: [], jobFailed: true };
      }
      return {
        imported: status.rowsImported ?? 0,
        failed: [],
        jobFailed: false,
      };
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("Import timed out — please refresh and check your transactions.");
}

// ─── CSV Import (Async Job Pipeline) ─────────────────────────────────────────

export async function importTransactions(file: File): Promise<UploadJobResponse> {
  if (isMock()) {
    await new Promise((r) => setTimeout(r, 600));
    return { jobId: "mock-job-id", status: "pending" };
  }

  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/transactions/import", { method: "POST", body: formData });
  if (!res.ok) throw new Error("Failed to start import");
  const json = await res.json();
  return { jobId: json.jobId, status: json.status };
}

export async function getImportJobStatus(jobId: string): Promise<ImportJobStatus> {
  if (isMock()) {
    return { jobId, status: "complete", rowsImported: 5, rowsUpdated: 0 };
  }

  const res = await fetch(`/api/transactions/import/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch import job status for ${jobId}`);
  const json = await res.json();
  return {
    jobId: json.jobId,
    status: json.status,
    rowsImported: json.rowsImported,
    rowsUpdated: json.rowsUpdated,
    errors: json.errors,
  };
}

export async function confirmImport(jobId: string): Promise<ImportJobStatus> {
  if (isMock()) {
    return { jobId, status: "complete", rowsImported: 5, rowsUpdated: 0 };
  }

  const res = await fetch(`/api/transactions/import/${jobId}/confirm`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to confirm import job ${jobId}`);
  const json = await res.json();
  return {
    jobId: json.jobId,
    status: json.status,
    rowsImported: json.rowsImported,
    rowsUpdated: json.rowsUpdated,
    errors: json.errors,
  };
}
