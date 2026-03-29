import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/formatters";
import type { MonthlySummary } from "@/types";
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const CHART_COLORS = [
  "#6366f1", // indigo
  "#f59e0b", // amber
  "#10b981", // emerald
  "#f43f5e", // rose
  "#3b82f6", // blue
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#14b8a6", // teal
  "#f97316", // orange
  "#84cc16", // lime
];

interface SpendingDonutProps {
  summary: MonthlySummary | undefined;
  isLoading: boolean;
}

interface TooltipPayloadEntry {
  name: string;
  value: number;
  payload: { fill: string };
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
}) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm">
      <p className="font-medium">{name}</p>
      <p className="text-muted-foreground">{formatCurrency(value)}</p>
    </div>
  );
}

export function SpendingDonut({ summary, isLoading }: SpendingDonutProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <Skeleton className="h-4 w-40" />
        <div className="flex justify-center">
          <Skeleton className="h-56 w-56 rounded-full" />
        </div>
      </div>
    );
  }

  if (!summary) return null;

  const data = summary.byCategory
    .filter((c) => c.amount > 0)
    .sort((a, b) => b.amount - a.amount);

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-sm font-medium text-muted-foreground mb-4">Spending by Category</h2>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            dataKey="amount"
            nameKey="categoryName"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
          >
            {data.map((entry, i) => (
              <Cell key={entry.categoryId} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value) => (
              <span className="text-xs text-foreground">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
