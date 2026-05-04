import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Transaction } from "@/types";
import { Flag } from "lucide-react";

const MISSING_FIELD_LABELS: Record<string, string> = {
  description: "description",
  amount: "amount",
  authorizedDate: "date",
  primaryCategory: "category",
  detailedCategory: "detailed category",
};

function getMissingFields(tx: Transaction): string[] {
  const checks: Array<[string, boolean]> = [
    ["description", !tx.description],
    ["amount", tx.amount == null],
    ["authorizedDate", !tx.authorizedDate],
    ["primaryCategory", !tx.primaryCategory],
    ["detailedCategory", !tx.detailedCategory],
  ];
  return checks.filter(([, missing]) => missing).map(([key]) => MISSING_FIELD_LABELS[key]);
}

interface FlaggedTransactionsListProps {
  transactions: Transaction[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onEdit: (tx: Transaction) => void;
}

function RowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 flex-1" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-4 w-32" />
    </div>
  );
}

function FlaggedRow({ tx, onEdit }: { tx: Transaction; onEdit: (tx: Transaction) => void }) {
  const missing = getMissingFields(tx);
  return (
    <button
      type="button"
      onClick={() => onEdit(tx)}
      className="w-full flex flex-wrap items-center gap-3 py-3 border-b border-border last:border-0 hover:bg-muted/30 transition-colors text-left px-1 rounded"
    >
      <span className="text-xs text-muted-foreground w-24 shrink-0">{formatDate(tx.authorizedDate)}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{tx.description || <span className="italic text-muted-foreground">No description</span>}</p>
        {missing.length > 0 && (
          <p className="text-xs text-amber-600 dark:text-amber-400">Missing: {missing.join(", ")}</p>
        )}
      </div>
      <span className="text-sm font-medium tabular-nums text-red-600 dark:text-red-400 shrink-0">
        {tx.amount != null ? formatCurrency(tx.amount) : "—"}
      </span>
      <span className="text-xs text-muted-foreground shrink-0">Edit →</span>
    </button>
  );
}

export function FlaggedTransactionsList({
  transactions,
  isLoading,
  isError,
  onEdit,
}: FlaggedTransactionsListProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Flag size={15} className="text-amber-500" />
        <h2 className="text-sm font-medium">Flagged Transactions</h2>
        {!isLoading && transactions && (
          <Badge variant="secondary" className="ml-auto">
            {transactions.length}
          </Badge>
        )}
      </div>

      {isLoading && (
        <div>
          <RowSkeleton />
          <RowSkeleton />
          <RowSkeleton />
        </div>
      )}

      {isError && (
        <p className="text-sm text-muted-foreground text-center py-6">
          Failed to load flagged transactions.
        </p>
      )}

      {!isLoading && !isError && transactions?.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-6">
          No flagged transactions — you're all caught up!
        </p>
      )}

      {!isLoading && !isError && transactions && transactions.length > 0 && (
        <div>
          {transactions.map((tx) => (
            <FlaggedRow key={tx.id} tx={tx} onEdit={onEdit} />
          ))}
        </div>
      )}
    </div>
  );
}
