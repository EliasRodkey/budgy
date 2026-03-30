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
      </div>
    );
  }

  const budgeted = byCategory.filter((c) => c.monthlyLimit !== null);
  const totalBudget = budgeted.reduce((s, c) => s + c.monthlyLimit!, 0);
  const totalSpent = budgeted.reduce((s, c) => s + c.amount, 0);
  const remaining = totalBudget - totalSpent;
  const fillPct = totalBudget > 0 ? Math.min(totalSpent / totalBudget, 1) * 100 : 0;
  const isOver = remaining < 0;

  return (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col justify-center gap-4">
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

          <div className="w-full bg-muted rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                isOver ? "bg-destructive" : "bg-primary"
              }`}
              style={{ width: `${fillPct}%` }}
            />
          </div>
        </>
      )}
    </div>
  );
}
