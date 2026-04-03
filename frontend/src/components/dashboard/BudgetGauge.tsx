import { computeBudgetGauge } from "@/lib/budgetGauge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/formatters";
import type { CategorySpend } from "@/types";

interface BudgetGaugeProps {
  byCategory: CategorySpend[];
  isLoading: boolean;
}

export function BudgetGauge({ byCategory, isLoading }: BudgetGaugeProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <Skeleton className="h-4 w-36" />
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-3 w-full rounded-full" />
        <Skeleton className="h-3 w-full rounded-full" />
      </div>
    );
  }

  const { totalBudget, totalSpent, remaining, spentPct, remainingPct, isOver } =
    computeBudgetGauge(byCategory);

  return (
    <div
      className={`rounded-xl border p-5 flex flex-col gap-4 transition-colors ${
        isOver
          ? "border-destructive/40 bg-destructive/5"
          : "border-border bg-card"
      }`}
    >
      <h2 className="text-sm font-medium text-muted-foreground">Remaining Budget</h2>

      {totalBudget === 0 ? (
        <p className="text-sm text-muted-foreground">No budget limits set</p>
      ) : (
        <>
          <p
            className={`text-3xl font-semibold tabular-nums ${
              isOver
                ? "text-red-600 dark:text-red-400"
                : "text-green-600 dark:text-green-400"
            }`}
          >
            {isOver ? "-" : ""}
            {formatCurrency(Math.abs(remaining))}
          </p>

          <div className="space-y-3">
            {/* Spend bar */}
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">
                Spent {formatCurrency(totalSpent)}
              </span>
              <div className="relative w-full bg-muted rounded-full h-10">
                <div
                  className="absolute left-0 top-0 h-10 rounded-full bg-[#f43f5e]"
                  style={{ width: `${spentPct}%` }}
                />
                {isOver && (
                  <div className="absolute right-0 top-0 h-10 w-0.5 bg-destructive/70 rounded-full" />
                )}
              </div>
            </div>

            {/* Remaining bar */}
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">
                Remaining {formatCurrency(Math.max(remaining, 0))}
              </span>
              <div className="relative w-full bg-muted rounded-full h-10">
                <div
                  className="absolute left-0 top-0 h-10 rounded-full bg-[#10b981]"
                  style={{ width: `${remainingPct}%` }}
                />
              </div>
            </div>

            {/* Over-budget label */}
            {isOver && (
              <p className="text-xs font-medium text-destructive">
                +{formatCurrency(Math.abs(remaining))} over budget
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
