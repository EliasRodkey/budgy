import { Skeleton } from "@/components/ui/skeleton";
import { CATEGORY_COLORS, NON_SPENDING_CATEGORIES } from "@/lib/categoryColors";
import { formatCurrency } from "@/lib/formatters";
import type { CategorySpend } from "@/types";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

interface CategoryDonutProps {
  categories: CategorySpend[];
  isLoading: boolean;
  onCategoryClick?: (categoryName: string) => void;
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
}

interface TooltipPayloadEntry {
  name: string;
  value: number;
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

export function CategoryDonut({
  categories,
  isLoading,
  onCategoryClick,
  height = 340,
  innerRadius = 90,
  outerRadius = 150,
}: CategoryDonutProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 flex justify-center">
        <Skeleton className="rounded-full" style={{ width: outerRadius * 2, height: outerRadius * 2 }} />
      </div>
    );
  }

  const data = categories
    .filter((c) => !NON_SPENDING_CATEGORIES.has(c.categoryName) && c.amount > 0)
    .sort((a, b) => b.amount - a.amount);

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 flex items-center justify-center" style={{ height }}>
        <p className="text-sm text-muted-foreground">No spending data this month</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-sm font-medium text-muted-foreground mb-2 text-center">
        Spending by Category
      </h2>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey="amount"
            nameKey="categoryName"
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            cursor={onCategoryClick ? "pointer" : undefined}
            onClick={(entry) => onCategoryClick?.(entry.categoryName as string)}
          >
            {data.map((entry) => (
              <Cell
                key={entry.categoryId}
                fill={CATEGORY_COLORS[entry.categoryName] ?? "#94a3b8"}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
