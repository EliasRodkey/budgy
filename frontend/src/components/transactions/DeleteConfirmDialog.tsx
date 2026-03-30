import { Button } from "@/components/ui/button";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Transaction } from "@/types";
import { AlertTriangle, X } from "lucide-react";

interface DeleteConfirmDialogProps {
  transaction: Transaction | null;
  isPending: boolean;
  onConfirm: (id: string) => void;
  onClose: () => void;
}

export function DeleteConfirmDialog({ transaction, isPending, onConfirm, onClose }: DeleteConfirmDialogProps) {
  if (!transaction) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-destructive" />
            <h2 className="text-sm font-semibold">Delete Transaction</h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <p className="text-sm text-muted-foreground">
            Are you sure you want to delete this transaction? This action cannot be undone.
          </p>

          <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-1">
            <p className="text-sm font-medium">{transaction.description}</p>
            <p className="text-xs text-muted-foreground">{transaction.merchant} · {formatDate(transaction.date)}</p>
            <p className={`text-sm font-semibold tabular-nums ${transaction.amount < 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"}`}>
              {formatCurrency(transaction.amount)}
            </p>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={isPending}
              onClick={() => onConfirm(transaction.id)}
            >
              {isPending ? "Deleting…" : "Delete"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
