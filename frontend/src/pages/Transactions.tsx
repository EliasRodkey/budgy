import { importTransactions } from "@/api/transactions";
import { CSVUploadModal } from "@/components/transactions/CSVUploadModal";
import { DeleteConfirmDialog } from "@/components/transactions/DeleteConfirmDialog";
import { EditTransactionModal } from "@/components/transactions/EditTransactionModal";
import { TransactionTable } from "@/components/transactions/TransactionTable";
import { Button } from "@/components/ui/button";
import { ALL_DETAILED_CATEGORIES, CATEGORY_MAPPING } from "@/constants/categories";
import {
  useAvailableTags,
  useDeleteTransaction,
  useTransactions,
  useUpdateTransaction,
} from "@/hooks/useTransactions";
import type { Transaction } from "@/types";
import { AlertCircle, ArrowUpDown, RefreshCw, Upload } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";

const PAGE_SIZE = 20;

function PaginationControls({
  page,
  total,
  pageSize,
  onPageChange,
}: {
  page: number;
  total: number;
  pageSize: number;
  onPageChange: (p: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="flex items-center justify-between">
      <p className="text-xs text-muted-foreground">
        {total === 0 ? "0 results" : `${from}–${to} of ${total}`}
      </p>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <span className="text-xs text-muted-foreground px-2">
          {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Filter/sort/page state from URL
  const search = searchParams.get("search") ?? "";
  const category = searchParams.get("category") ?? "";
  const detailedCategory = searchParams.get("detailedCategory") ?? "";
  const tagsParam = searchParams.get("tags") ?? "";
  const showExcluded = searchParams.get("showExcluded") === "true";
  const dateFrom = searchParams.get("dateFrom") ?? "";
  const dateTo = searchParams.get("dateTo") ?? "";
  const sortBy = (searchParams.get("sortBy") as "date" | "amount") ?? "date";
  const sortOrder = (searchParams.get("sortOrder") as "asc" | "desc") ?? "desc";
  const page = Number(searchParams.get("page") ?? "1");

  // Parse comma-separated tags from URL
  const filterTags = tagsParam ? tagsParam.split(",").filter(Boolean) : [];

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
      if (key !== "page") next.set("page", "1");
      return next;
    });
  }

  function toggleSort(field: "date" | "amount") {
    if (sortBy === field) {
      setParam("sortOrder", sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set("sortBy", field);
        next.set("sortOrder", "desc");
        next.set("page", "1");
        return next;
      });
    }
  }

  // Detailed category options depend on selected primary category
  const detailedCategoryOptions = category
    ? (CATEGORY_MAPPING[category] ?? [])
    : ALL_DETAILED_CATEGORIES;

  const { data, isLoading, isError, refetch } = useTransactions({
    search: search || undefined,
    category: category || undefined,
    detailedCategory: detailedCategory || undefined,
    tags: filterTags.length > 0 ? filterTags : undefined,
    showExcluded,
    dateFrom: dateFrom || undefined,
    dateTo: dateTo || undefined,
    sortBy,
    sortOrder,
    page,
    pageSize: PAGE_SIZE,
  });

  const { data: availableTags = [] } = useAvailableTags();
  const { mutate: updateTx, isPending: updatePending } = useUpdateTransaction();
  const { mutate: deleteTx, isPending: deletePending } = useDeleteTransaction();

  const [editTarget, setEditTarget] = useState<Transaction | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Transaction | null>(null);
  const [showImport, setShowImport] = useState(false);

  function handleSave(id: string, updates: Partial<Transaction>) {
    updateTx({ id, updates }, { onSuccess: () => setEditTarget(null) });
  }

  function handleDelete(id: string) {
    deleteTx(id, { onSuccess: () => setDeleteTarget(null) });
  }

  return (
    <div className="p-6 space-y-5 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Transactions</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Search, filter, and manage your transactions
          </p>
        </div>
        <Button onClick={() => setShowImport(true)}>
          <Upload size={14} className="mr-1.5" />
          Import CSV
        </Button>
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-3">
        {/* Row 1: search + primary category */}
        <div className="flex flex-wrap gap-3">
          <input
            type="search"
            placeholder="Search description or merchant…"
            value={search}
            onChange={(e) => setParam("search", e.target.value)}
            className="h-8 flex-1 min-w-48 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <select
            value={category}
            onChange={(e) => {
              // Single setSearchParams call — two calls in one handler don't chain correctly
              setSearchParams((prev) => {
                const next = new URLSearchParams(prev);
                if (e.target.value) {
                  next.set("category", e.target.value);
                } else {
                  next.delete("category");
                }
                next.delete("detailedCategory");
                next.set("page", "1");
                return next;
              });
            }}
            className="h-8 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All categories</option>
            {Object.keys(CATEGORY_MAPPING).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={detailedCategory}
            onChange={(e) => setParam("detailedCategory", e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All detailed categories</option>
            {detailedCategoryOptions.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* Row 2: dates + tag filter + show excluded + sort */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground whitespace-nowrap">From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setParam("dateFrom", e.target.value)}
              className="h-8 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground whitespace-nowrap">To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setParam("dateTo", e.target.value)}
              className="h-8 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <input
            type="search"
            placeholder="Filter by tag…"
            value={tagsParam}
            onChange={(e) => setParam("tags", e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring w-36"
          />

          <label className="flex items-center gap-2 text-sm cursor-pointer whitespace-nowrap">
            <input
              type="checkbox"
              checked={showExcluded}
              onChange={(e) => setParam("showExcluded", e.target.checked ? "true" : "")}
              className="rounded border-input"
            />
            <span className="text-xs text-muted-foreground">Show excluded</span>
          </label>

          <div className="flex items-center gap-1 ml-auto">
            <ArrowUpDown size={13} className="text-muted-foreground" />
            <span className="text-xs text-muted-foreground mr-1">Sort:</span>
            <button
              onClick={() => toggleSort("date")}
              className={`text-xs px-2 py-1 rounded-md transition-colors ${
                sortBy === "date"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80 text-muted-foreground"
              }`}
            >
              Date {sortBy === "date" ? (sortOrder === "asc" ? "↑" : "↓") : ""}
            </button>
            <button
              onClick={() => toggleSort("amount")}
              className={`text-xs px-2 py-1 rounded-md transition-colors ${
                sortBy === "amount"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80 text-muted-foreground"
              }`}
            >
              Amount {sortBy === "amount" ? (sortOrder === "asc" ? "↑" : "↓") : ""}
            </button>
          </div>
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load transactions.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      {/* Transaction table */}
      {!isError && (
        <TransactionTable
          transactions={data?.data ?? []}
          isLoading={isLoading}
          onEdit={setEditTarget}
          onDelete={setDeleteTarget}
        />
      )}

      {/* Pagination */}
      {!isError && !isLoading && (
        <PaginationControls
          page={page}
          total={data?.total ?? 0}
          pageSize={PAGE_SIZE}
          onPageChange={(p) => setParam("page", String(p))}
        />
      )}

      {/* Modals */}
      <EditTransactionModal
        transaction={editTarget}
        isPending={updatePending}
        availableTags={availableTags}
        onSave={handleSave}
        onClose={() => setEditTarget(null)}
      />
      <DeleteConfirmDialog
        transaction={deleteTarget}
        isPending={deletePending}
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
      {showImport && (
        <CSVUploadModal
          onImport={importTransactions}
          onClose={() => setShowImport(false)}
        />
      )}
    </div>
  );
}
