import { Button } from "@/components/ui/button";
import { tagPillStyle } from "@/lib/tagColors";
import type { Transaction } from "@/types";
import { X } from "lucide-react";
import { useState } from "react";

export type BulkApplyScope = "all" | "no_existing" | "only_this" | "select";

export interface BulkApplyChange {
  newTags: string[];          // tags that were added
  primaryCategory?: string;   // new primary category (if changed)
  detailedCategory?: string;  // new detailed category (if changed)
}

interface BulkApplyDialogProps {
  /** The transaction that was just saved. */
  transaction: Transaction;
  /** Other transactions sharing the same description + accountName. */
  similarTransactions: Transaction[];
  /** What was changed. */
  change: BulkApplyChange;
  isPending: boolean;
  onConfirm: (scope: BulkApplyScope, selectedIds: number[], saveAsRule: boolean) => void;
  onClose: () => void;
}

export function BulkApplyDialog({
  transaction,
  similarTransactions,
  change,
  isPending,
  onConfirm,
  onClose,
}: BulkApplyDialogProps) {
  const [scope, setScope] = useState<BulkApplyScope>("all");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(
    new Set(similarTransactions.map((t) => Number(t.id))),
  );
  const [saveAsRule, setSaveAsRule] = useState(true);

  const hasTags = change.newTags.length > 0;
  const hasCategory = !!(change.primaryCategory || change.detailedCategory);

  function toggleId(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleConfirm() {
    onConfirm(scope, [...selectedIds], saveAsRule);
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border shrink-0">
          <h2 className="text-sm font-semibold">Apply to similar transactions?</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <div className="p-5 flex-1 overflow-y-auto space-y-4">
          {/* Summary of what changed */}
          <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-1.5 text-xs">
            <p className="font-medium text-muted-foreground">Changes made to this transaction:</p>
            {hasTags && (
              <div className="flex flex-wrap gap-1 items-center">
                <span className="text-muted-foreground">Tags added:</span>
                {change.newTags.map((tag) => (
                  <span key={tag} style={tagPillStyle(tag)} className="rounded-full border px-2 py-0.5 text-xs font-medium">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            {hasCategory && (
              <p className="text-muted-foreground">
                Category:{" "}
                <span className="font-medium text-foreground">
                  {[change.primaryCategory, change.detailedCategory].filter(Boolean).join(" › ")}
                </span>
              </p>
            )}
          </div>

          <p className="text-xs text-muted-foreground">
            Found <strong>{similarTransactions.length}</strong> other transaction
            {similarTransactions.length !== 1 ? "s" : ""} from{" "}
            <strong className="text-foreground">&ldquo;{transaction.description}&rdquo;</strong>{" "}
            on <strong className="text-foreground">{transaction.accountName}</strong>.
          </p>

          {/* Scope radio options */}
          <div className="space-y-2">
            {(
              [
                ["all", "Apply to all matching transactions"],
                ["no_existing", hasTags ? "Apply only to those with no tags yet" : "Apply only to those with no category yet"],
                ["only_this", "Only this transaction (already saved)"],
                ["select", "Select specific transactions"],
              ] as [BulkApplyScope, string][]
            ).map(([value, label]) => (
              <label key={value} className="flex items-start gap-2.5 cursor-pointer group">
                <input
                  type="radio"
                  name="bulk-scope"
                  value={value}
                  checked={scope === value}
                  onChange={() => setScope(value)}
                  className="mt-0.5 shrink-0"
                />
                <span className="text-sm group-hover:text-foreground transition-colors">{label}</span>
              </label>
            ))}
          </div>

          {/* Select list */}
          {scope === "select" && (
            <div className="rounded-lg border border-border overflow-hidden">
              <ul className="max-h-48 overflow-y-auto divide-y divide-border">
                {similarTransactions.map((tx) => (
                  <li key={tx.id}>
                    <label className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-muted/30 transition-colors">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(Number(tx.id))}
                        onChange={() => toggleId(Number(tx.id))}
                        className="shrink-0"
                      />
                      <div className="min-w-0">
                        <p className="text-xs font-medium truncate">{tx.description}</p>
                        <p className="text-xs text-muted-foreground">{tx.authorizedDate}</p>
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Save as rule */}
          {scope !== "only_this" && (
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={saveAsRule}
                onChange={(e) => setSaveAsRule(e.target.checked)}
                className="rounded border-input"
              />
              <span className="text-xs text-muted-foreground">
                Remember this rule for future imports
              </span>
            </label>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-5 border-t border-border shrink-0">
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            Skip
          </Button>
          <Button onClick={handleConfirm} disabled={isPending || (scope === "select" && selectedIds.size === 0)}>
            {isPending ? "Applying…" : scope === "only_this" ? "Done" : "Apply"}
          </Button>
        </div>
      </div>
    </div>
  );
}
