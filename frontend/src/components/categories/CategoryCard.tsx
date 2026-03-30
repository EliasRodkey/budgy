import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/formatters";
import type { CategorySpend } from "@/types";

interface CategoryCardProps {
  spend: CategorySpend;
  color?: string;
  onClick?: () => void;
}

export function CategoryCard({ spend, color, onClick }: CategoryCardProps) {
  const hasLimit = spend.monthlyLimit !== null && spend.percentOfLimit !== null;
  const pct = spend.percentOfLimit ?? 0;
  const overBudget = spend.isOverBudget;
  const barWidth = Math.min(pct, 100);

  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-xl border border-border bg-card p-5 hover:bg-muted/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          {color && (
            <span
              className="shrink-0 inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: color }}
            />
          )}
          <h3 className="text-sm font-medium truncate">{spend.categoryName}</h3>
        </div>
        {overBudget && (
          <span className="shrink-0 inline-flex items-center rounded-full bg-destructive/15 px-2 py-0.5 text-[10px] font-semibold text-destructive">
            Over budget
          </span>
        )}
      </div>

      <p className="text-2xl font-semibold tabular-nums">
        {formatCurrency(spend.amount)}
      </p>

      <div className="mt-3 space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          {hasLimit ? (
            <>
              <span>{Math.round(pct)}% of limit</span>
              <span>{formatCurrency(spend.monthlyLimit!)} limit</span>
            </>
          ) : (
            <span>No budget set</span>
          )}
        </div>
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          {hasLimit && (
            <div
              className={`h-full rounded-full transition-all ${
                overBudget ? "bg-destructive" : "bg-primary"
              }`}
              style={{ width: `${barWidth}%` }}
            />
          )}
        </div>
      </div>

      <p className="mt-2 text-xs text-muted-foreground">
        {spend.transactionCount} transaction{spend.transactionCount !== 1 ? "s" : ""}
      </p>
    </button>
  );
}

export function CategoryCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-1.5 w-full" />
    </div>
  );
}
