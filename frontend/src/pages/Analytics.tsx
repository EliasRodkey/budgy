import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MOCK_DEFAULT_DATE_FROM, MOCK_DEFAULT_DATE_TO } from "@/api/analytics";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useSummary } from "@/hooks/useSummary";
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
  Pie,
  PieChart,
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

  const dateFrom = searchParams.get("dateFrom") ?? MOCK_DEFAULT_DATE_FROM;
  const dateTo = searchParams.get("dateTo") ?? MOCK_DEFAULT_DATE_TO;
  const donutMonth = searchParams.get("donutMonth") ?? dateTo;

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set(key, value);
      return next;
    });
  }

  const { data, isLoading, isError, refetch } = useAnalytics({ dateFrom, dateTo });
  const { data: donutSummary, isLoading: donutLoading } = useSummary(donutMonth);

  const labels = data?.series.labels ?? [];
  const datasets = data?.series.datasets ?? [];
  const incomeExpenses = data?.incomeExpenses ?? [];

  // Build flat data arrays for charts that use month as x-axis
  const incomeExpensesChartData = incomeExpenses.map((row) => ({
    month: row.month,
    Income: row.income,
    Expenses: row.expenses,
    Net: row.net,
  }));

  // Stacked bar and line chart share the same flat row shape
  const flatChartData = labels.map((label, labelIdx) => {
    const row: Record<string, string | number> = { month: label };
    for (const ds of datasets) {
      row[ds.categoryName] = ds.values[labelIdx] ?? 0;
    }
    return row;
  });

  // Donut data from selected month summary
  const donutData =
    donutSummary?.byCategory
      .filter((c) => c.amount > 0)
      .sort((a, b) => b.amount - a.amount) ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Header + date range selector */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Spending trends and summaries across your selected period.
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
        <ChartSkeleton height={300} />
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
            <ResponsiveContainer width="100%" height={300}>
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

      {/* 2. Income vs expenses + 3. Donut side by side */}
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

        {/* Donut chart for selected month */}
        {donutLoading ? (
          <ChartSkeleton height={280} />
        ) : (
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-muted-foreground">
                Category Breakdown
              </h2>
              {labels.length > 0 && (
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-muted-foreground text-right">Month</label>
                  <select
                    value={donutMonth}
                    onChange={(e) => setParam("donutMonth", e.target.value)}
                    className="rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {labels.map((label) => (
                      <option key={label} value={label}>
                        {formatMonth(label)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            {donutData.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-16">
                No spending data for {formatMonth(donutMonth)}.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={donutData}
                    dataKey="amount"
                    nameKey="categoryName"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                  >
                    {donutData.map((entry, i) => (
                      <Cell
                        key={entry.categoryId}
                        fill={categoryColor(entry.categoryName, i)}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const entry = payload[0];
                      return (
                        <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm">
                          <p className="font-medium">{entry.name}</p>
                          <p className="text-muted-foreground">
                            {formatCurrency(entry.value as number)}
                          </p>
                        </div>
                      );
                    }}
                  />
                  <Legend
                    formatter={(value) => (
                      <span className="text-xs text-foreground">{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </div>

      {/* 4. Stacked bar chart: category spending by month */}
      {isLoading ? (
        <ChartSkeleton height={300} />
      ) : (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">
            Category Spending by Month
          </h2>
          {flatChartData.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-16">
              No data for selected range.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={flatChartData}>
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
                  <Bar
                    key={ds.categoryId}
                    dataKey={ds.categoryName}
                    stackId="a"
                    fill={categoryColor(ds.categoryName, i)}
                    radius={i === datasets.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* 5. Small-multiple line charts: one per category */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ChartSkeleton key={i} height={160} />
          ))}
        </div>
      ) : datasets.length > 0 ? (
        <div>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            Per-Category Trends
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {datasets.map((ds, i) => {
              const chartData = labels.map((label, labelIdx) => ({
                month: label,
                value: ds.values[labelIdx] ?? 0,
              }));
              const color = categoryColor(ds.categoryName, i);
              return (
                <div
                  key={ds.categoryId}
                  className="rounded-xl border border-border bg-card p-4"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="inline-block h-2.5 w-2.5 shrink-0 rounded-sm"
                      style={{ backgroundColor: color }}
                    />
                    <h3 className="text-xs font-medium text-foreground">
                      {ds.categoryName}
                    </h3>
                  </div>
                  <ResponsiveContainer width="100%" height={160}>
                    <LineChart data={chartData}>
                      <XAxis
                        dataKey="month"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v: string) => v.slice(5)}
                      />
                      <YAxis
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) => `$${v}`}
                        width={50}
                      />
                      <Tooltip
                        content={({ active, payload, label: ttLabel }) => {
                          if (!active || !payload?.length) return null;
                          return (
                            <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-xs">
                              <p className="font-medium">{formatMonth(ttLabel as string)}</p>
                              <p className="text-muted-foreground">
                                {formatCurrency(payload[0].value as number)}
                              </p>
                            </div>
                          );
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={color}
                        strokeWidth={2}
                        dot={{ r: 3, fill: color }}
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
