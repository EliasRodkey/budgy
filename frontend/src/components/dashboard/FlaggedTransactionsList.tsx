import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Transaction } from "@/types";
import { Flag } from "lucide-react";
import { useState } from "react";

// Primary category options — mirrors the backend enum
const PRIMARY_CATEGORIES = [
  "Food & drink",
  "Transportation",
  "Housing & utilities",
  "Health & wellness",
  "Entertainment",
  "Shopping",
  "Services",
  "Insurance",
  "Investments",
  "Debt payments",
  "Transfers",
  "Travel",
  "Government & charity",
  "Bank fees",
  "Other",
];

interface FlaggedTransactionsListProps {
  transactions: Transaction[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onAssign: (transactionId: string, primaryCategory: string, detailedCategory: string) => void;
  isPending: boolean;
}

function RowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 flex-1" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-7 w-32 rounded-lg" />
    </div>
  );
}

interface AssignRowProps {
  tx: Transaction;
  onAssign: (transactionId: string, primaryCategory: string, detailedCategory: string) => void;
  isPending: boolean;
}

function AssignRow({ tx, onAssign, isPending }: AssignRowProps) {
  const [selected, setSelected] = useState("");

  return (
    <div className="flex flex-wrap items-center gap-3 py-3 border-b border-border last:border-0">
      <span className="text-xs text-muted-foreground w-24 shrink-0">{formatDate(tx.authorizedDate)}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{tx.description}</p>
        <p className="text-xs text-muted-foreground">{tx.account_name}</p>
      </div>
      <span className="text-sm font-medium tabular-nums text-red-600 dark:text-red-400 shrink-0">
        {formatCurrency(tx.amount)}
      </span>
      <div className="flex items-center gap-2 shrink-0">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="h-7 rounded-md border border-input bg-background px-2 text-xs focus:outline-none focus:ring-2 focus:ring-ring"
          aria-label={`Category for ${tx.description}`}
        >
          <option value="">Pick category…</option>
          {PRIMARY_CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
        <Button
          size="xs"
          disabled={!selected || isPending}
          onClick={() => onAssign(tx.id, selected, selected)}
        >
          Assign
        </Button>
      </div>
    </div>
  );
}

export function FlaggedTransactionsList({
  transactions,
  isLoading,
  isError,
  onAssign,
  isPending,
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
            <AssignRow key={tx.id} tx={tx} onAssign={onAssign} isPending={isPending} />
          ))}
        </div>
      )}
    </div>
  );
}
