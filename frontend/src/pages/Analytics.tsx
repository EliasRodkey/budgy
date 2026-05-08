import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getDefaultDateRange } from "@/api/analytics";
import { useAnalytics } from "@/hooks/useAnalytics";
import { formatCurrency, formatMonth } from "@/lib/formatters";
import { AlertCircle, RefreshCw } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useSearchParams } from "react-router-dom";

// ─── Colors ───────────────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<string, string> = {
  "Food & drink": "#f97316",
  "Housing & utilities": "#8b5cf6",
  Transportation: "#3b82f6",
  "Health & wellness": "#22c55e",
  Entertainment: "#ec4899",
  Shopping: "#f59e0b",
  Insurance: "#06b6d4",
  Services: "#6366f1",
  Travel: "#84cc16",
  "Government & charity": "#ef4444",
  Transfers: "#94a3b8",
  "Debt payments": "#dc2626",
  Investments: "#10b981",
  "Bank fees": "#f43f5e",
  Other: "#6b7280",
  Income: "#4ade80",
};

const FALLBACK_COLORS = [
  "#6366f1",
  "#f59e0b",
  "#10b981",
  "#f43f5e",
  "#3b82f6",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#84cc16",
];

function categoryColor(name: string, idx: number): string {
  return CATEGORY_COLORS[name] ?? FALLBACK_COLORS[idx % FALLBACK_COLORS.length];
}

// ─── Shared tooltip ───────────────────────────────────────────────────────────

interface TooltipEntry {
  name: string;
  value: number;
  color?: string;
  fill?: string;
  stroke?: string;
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm min-w-[160px]">
      {label && <p className="font-medium mb-1">{formatMonth(label)}</p>}
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-sm"
              style={{ backgroundColor: entry.color ?? entry.fill ?? entry.stroke }}
            />
            <span className="text-muted-foreground">{entry.name}</span>
          </span>
          <span className="font-medium">{formatCurrency(entry.value)}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Skeleton card ────────────────────────────────────────────────────────────

function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <Skeleton className="h-4 w-48" />
      <Skeleton style={{ height }} className="w-full rounded-lg" />
    </div>
  );
}

// ─── Error card ───────────────────────────────────────────────────────────────

function ErrorCard({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
        <p className="text-sm text-destructive">Failed to load analytics data.</p>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry} className="gap-1.5">
        <RefreshCw className="h-3.5 w-3.5" />
        Retry
      </Button>
    </div>
  );
}

// ─── Analytics page ───────────────────────────────────────────────────────────

export default function Analytics() {
  const [searchParams, setSearchParams] = useSearchParams();

  const defaults = getDefaultDateRange();
  const dateFrom = searchParams.get("dateFrom") ?? defaults.from;
  const dateTo = searchParams.get("dateTo") ?? defaults.to;

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set(key, value);
      return next;
    });
  }

  const { data, isLoading, isError, refetch } = useAnalytics({ dateFrom, dateTo });

  const labels = data?.series.labels ?? [];
  const datasets = data?.series.datasets ?? [];
  const incomeExpenses = data?.incomeExpenses ?? [];
  const budgetPerformance = data?.budgetPerformance ?? [];
  const monthlyBudgetTotals = data?.monthlyBudgetTotals ?? [];

  // Build flat data arrays for charts that use month as x-axis
  const incomeExpensesChartData = incomeExpenses.map((row) => ({
    month: row.month,
    Income: row.income,
    Expenses: row.expenses,
    Net: row.net,
  }));

  const flatChartData = labels.map((label, labelIdx) => {
    const row: Record<string, string | number> = { month: label };
    for (const ds of datasets) {
      row[ds.categoryName] = ds.values[labelIdx] ?? 0;
    }
    return row;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header + date range selector */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Spending trends and budget performance across your selected period.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">From</label>
            <input
              type="month"
              value={dateFrom}
              max={dateTo}
              onChange={(e) => setParam("dateFrom", e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">To</label>
            <input
              type="month"
              value={dateTo}
              min={dateFrom}
              onChange={(e) => setParam("dateTo", e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      </div>

      {isError && <ErrorCard onRetry={() => refetch()} />}

      {/* 1. Line chart: spending over time per category */}
      {isLoading ? (
        <ChartSkeleton height={450} />
      ) : (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">
            Spending Over Time by Category
          </h2>
          {flatChartData.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-16">
              No data for selected range.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={450}>
              <LineChart data={flatChartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  tickFormatter={formatMonth}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v) => formatCurrency(v)}
                  width={80}
                />
                <Tooltip content={<ChartTooltip />} />
                <Legend />
                {datasets.map((ds, i) => (
                  <Line
                    key={ds.categoryId}
                    type="monotone"
                    dataKey={ds.categoryName}
                    stroke={categoryColor(ds.categoryName, i)}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* 2. Income vs expenses + 3. Total over/under budget side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income vs Expenses bar chart with net overlay */}
        {isLoading ? (
          <ChartSkeleton height={280} />
        ) : (
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-medium text-muted-foreground mb-4">
              Income vs. Expenses
            </h2>
            {incomeExpensesChartData.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-16">
                No data for selected range.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={incomeExpensesChartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    tickFormatter={formatMonth}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v) => formatCurrency(v)}
                    width={80}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend />
                  <Bar dataKey="Income" fill="#4ade80" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Expenses" fill="#f43f5e" radius={[3, 3, 0, 0]} />
                  <Line
                    type="monotone"
                    dataKey="Net"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        {/* Total over/under budget bar chart */}
        {isLoading ? (
          <ChartSkeleton height={280} />
        ) : (
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-medium text-muted-foreground mb-4">
              Total Over/Under Budget
            </h2>
            {monthlyBudgetTotals.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-16">
                No budget data for selected range.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={monthlyBudgetTotals}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    tickFormatter={formatMonth}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v) => formatCurrency(v)}
                    width={80}
                  />
                  <ReferenceLine y={0} stroke="currentColor" strokeOpacity={0.3} />
                  <Tooltip
                    content={({ active, payload, label: ttLabel }) => {
                      if (!active || !payload?.length) return null;
                      const val = payload[0].value as number;
                      const isOver = val > 0;
                      return (
                        <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm min-w-[180px]">
                          <p className="font-medium mb-1">
                            {formatMonth(ttLabel as string)}
                          </p>
                          <div className="flex items-center justify-between gap-4">
                            <span className="text-muted-foreground">
                              {isOver ? "Over budget" : "Under budget"}
                            </span>
                            <span
                              className="font-medium"
                              style={{ color: isOver ? "#f43f5e" : "#22c55e" }}
                            >
                              {isOver ? "+" : ""}
                              {formatCurrency(val)}
                            </span>
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="overUnder" radius={[3, 3, 0, 0]} name="Over/Under Budget">
                    {monthlyBudgetTotals.map((entry, i) => (
                      <Cell
                        key={`cell-${i}`}
                        fill={entry.overUnder > 0 ? "#f43f5e" : "#22c55e"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </div>

      {/* 4. Per-category budget performance cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ChartSkeleton key={i} height={160} />
          ))}
        </div>
      ) : budgetPerformance.length > 0 ? (
        <div>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            Per-Category Budget Performance
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {budgetPerformance.map((cat, i) => {
              const color = categoryColor(cat.categoryName, i);
              // For income: positive is good (green). For expenses: positive is bad (red).
              const isAvgOver = cat.isIncome
                ? cat.averageOverUnder < 0
                : cat.averageOverUnder > 0;
              const avgBadgeColor = isAvgOver ? "#f43f5e" : "#22c55e";
              const avgBadgeBg = isAvgOver
                ? "rgba(244,63,94,0.12)"
                : "rgba(34,197,94,0.12)";
              return (
                <div
                  key={cat.categoryId}
                  className="rounded-xl border border-border bg-card p-4"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className="inline-block h-2.5 w-2.5 shrink-0 rounded-sm"
                        style={{ backgroundColor: color }}
                      />
                      <h3 className="text-xs font-medium text-foreground truncate">
                        {cat.categoryName}
                      </h3>
                    </div>
                    <span
                      className="text-xs font-medium shrink-0 px-1.5 py-0.5 rounded-full"
                      style={{ backgroundColor: avgBadgeBg, color: avgBadgeColor }}
                    >
                      {cat.averageOverUnder > 0 ? "+" : ""}
                      {formatCurrency(cat.averageOverUnder)} avg
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    {cat.isIncome
                      ? `Estimate: ${formatCurrency(cat.monthlyLimit)}/mo`
                      : `Budget: ${formatCurrency(cat.monthlyLimit)}/mo`}
                  </p>
                  <ResponsiveContainer width="100%" height={140}>
                    <LineChart data={cat.data}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                      <XAxis
                        dataKey="month"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v: string) => {
                          const [year, mon] = v.split("-").map(Number);
                          return new Date(year, mon - 1, 1).toLocaleDateString(
                            "en-US",
                            { month: "short" },
                          );
                        }}
                      />
                      <YAxis
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) => formatCurrency(v)}
                        width={60}
                      />
                      <ReferenceLine
                        y={0}
                        stroke="currentColor"
                        strokeOpacity={0.4}
                        strokeDasharray="4 2"
                      />
                      <Tooltip
                        content={({ active, payload, label: ttLabel }) => {
                          if (!active || !payload?.length) return null;
                          const val = payload[0].value as number;
                          // For income: positive = above estimate (good). For expenses: positive = over budget (bad).
                          const isPositive = val > 0;
                          const isWarning = cat.isIncome ? !isPositive : isPositive;
                          const labelText = cat.isIncome
                            ? isPositive
                              ? "Above estimate"
                              : "Below estimate"
                            : isPositive
                              ? "Over budget"
                              : "Under budget";
                          return (
                            <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-xs min-w-[160px]">
                              <p className="font-medium mb-1">
                                {formatMonth(ttLabel as string)}
                              </p>
                              <div className="flex items-center justify-between gap-3">
                                <span className="text-muted-foreground">
                                  {labelText}
                                </span>
                                <span
                                  className="font-medium"
                                  style={{
                                    color: isWarning ? "#f43f5e" : "#22c55e",
                                  }}
                                >
                                  {val > 0 ? "+" : ""}
                                  {formatCurrency(val)}
                                </span>
                              </div>
                            </div>
                          );
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="overUnder"
                        stroke={color}
                        strokeWidth={2}
                        dot={{ r: 3, fill: color }}
                        activeDot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
