import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/formatters";
import type { MonthlySummary } from "@/types";
import { TrendingDown, TrendingUp, Wallet } from "lucide-react";

interface SummaryCardsProps {
  summary: MonthlySummary | undefined;
  isLoading: boolean;
}

function CardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-36" />
      <Skeleton className="h-3 w-16" />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  valueClass?: string;
}

function StatCard({ label, value, icon, valueClass }: StatCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-muted-foreground">{icon}</span>
      </div>
      <p className={`text-2xl font-semibold tabular-nums ${valueClass ?? ""}`}>
        {formatCurrency(value)}
      </p>
    </div>
  );
}

export function SummaryCards({ summary, isLoading }: SummaryCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        label="Income"
        value={summary.totalIncome}
        icon={<TrendingUp size={16} />}
        valueClass="text-green-600 dark:text-green-400"
      />
      <StatCard
        label="Expenses"
        value={-summary.totalExpenses}
        icon={<TrendingDown size={16} />}
        valueClass="text-red-600 dark:text-red-400"
      />
      <StatCard
        label="Net"
        value={summary.net}
        icon={<Wallet size={16} />}
        valueClass={summary.net >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}
      />
    </div>
  );
}
