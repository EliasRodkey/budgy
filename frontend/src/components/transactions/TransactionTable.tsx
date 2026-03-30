import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Transaction } from "@/types";
import { Flag, Pencil, Trash2 } from "lucide-react";

interface TransactionTableProps {
  transactions: Transaction[];
  isLoading: boolean;
  onEdit: (tx: Transaction) => void;
  onDelete: (tx: Transaction) => void;
}

function RowSkeleton() {
  return (
    <tr className="border-b border-border">
      <td className="py-3 px-4"><Skeleton className="h-4 w-24" /></td>
      <td className="py-3 px-4"><Skeleton className="h-4 w-48" /></td>
      <td className="py-3 px-4 text-right"><Skeleton className="h-4 w-20 ml-auto" /></td>
      <td className="py-3 px-4"><Skeleton className="h-5 w-28 rounded-full" /></td>
      <td className="py-3 px-4"><Skeleton className="h-5 w-24 rounded-full" /></td>
      <td className="py-3 px-4"><Skeleton className="h-4 w-6" /></td>
      <td className="py-3 px-4"><Skeleton className="h-7 w-16" /></td>
    </tr>
  );
}

interface RowProps {
  tx: Transaction;
  onEdit: (tx: Transaction) => void;
  onDelete: (tx: Transaction) => void;
}

function TransactionRow({ tx, onEdit, onDelete }: RowProps) {
  const isExpense = tx.amount < 0;
  return (
    <tr className="border-b border-border hover:bg-muted/30 transition-colors group">
      <td className="py-3 px-4 text-sm text-muted-foreground whitespace-nowrap">
        {formatDate(tx.date)}
      </td>
      <td className="py-3 px-4 max-w-xs">
        <p className="text-sm font-medium truncate">{tx.description}</p>
        <p className="text-xs text-muted-foreground truncate">{tx.merchant}</p>
      </td>
      <td className={`py-3 px-4 text-sm font-medium tabular-nums text-right whitespace-nowrap ${isExpense ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"}`}>
        {formatCurrency(tx.amount)}
      </td>
      <td className="py-3 px-4">
        <Badge variant="secondary" className="text-xs whitespace-nowrap">
          {tx.primaryCategory}
        </Badge>
      </td>
      <td className="py-3 px-4">
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {tx.detailedCategory}
        </span>
      </td>
      <td className="py-3 px-4">
        {tx.isFlagged && (
          <Flag size={14} className="text-amber-500" aria-label="Flagged" />
        )}
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="xs" onClick={() => onEdit(tx)} aria-label="Edit transaction">
            <Pencil size={13} />
          </Button>
          <Button variant="ghost" size="xs" onClick={() => onDelete(tx)} aria-label="Delete transaction" className="text-destructive hover:text-destructive">
            <Trash2 size={13} />
          </Button>
        </div>
      </td>
    </tr>
  );
}

export function TransactionTable({ transactions, isLoading, onEdit, onDelete }: TransactionTableProps) {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="py-3 px-4 text-xs font-medium text-muted-foreground">Date</th>
              <th className="py-3 px-4 text-xs font-medium text-muted-foreground">Description</th>
              <th className="py-3 px-4 text-xs font-medium text-muted-foreground text-right">Amount</th>
              <th className="py-3 px-4 text-xs font-medium text-muted-foreground">Category</th>
              <th className="py-3 px-4 text-xs font-medium text-muted-foreground">Subcategory</th>
              <th className="py-3 px-4 text-xs font-medium text-muted-foreground">Flag</th>
              <th className="py-3 px-4" />
            </tr>
          </thead>
          <tbody>
            {isLoading && Array.from({ length: 8 }).map((_, i) => <RowSkeleton key={i} />)}
            {!isLoading && transactions.length === 0 && (
              <tr>
                <td colSpan={7} className="py-16 text-center text-sm text-muted-foreground">
                  No transactions match your filters.
                </td>
              </tr>
            )}
            {!isLoading && transactions.map((tx) => (
              <TransactionRow key={tx.id} tx={tx} onEdit={onEdit} onDelete={onDelete} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
