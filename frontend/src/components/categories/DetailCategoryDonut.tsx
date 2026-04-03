import { Skeleton } from "@/components/ui/skeleton";
import { getCategoryShades } from "@/lib/categoryColors";
import { formatCurrency } from "@/lib/formatters";
import type { CategorySpend } from "@/types";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

interface DetailCategoryDonutProps {
  subcategories: CategorySpend[];
  baseColor: string;
  isLoading: boolean;
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

export function DetailCategoryDonut({
  subcategories,
  baseColor,
  isLoading,
}: DetailCategoryDonutProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 h-full flex flex-col gap-3">
        <Skeleton className="h-3 w-36 mx-auto" />
        <Skeleton className="rounded-full mx-auto" style={{ width: 120, height: 120 }} />
        <div className="space-y-2 mt-1">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-3 w-full" />
          ))}
        </div>
      </div>
    );
  }

  const data = subcategories.filter((c) => c.amount > 0).sort((a, b) => b.amount - a.amount);
  const shades = getCategoryShades(baseColor, data.length);

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 h-full flex items-center justify-center">
        <p className="text-sm text-muted-foreground">No spending data this month</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5 h-full flex flex-col">
      <h2 className="text-sm font-medium text-muted-foreground mb-2 text-center">
        By Subcategory
      </h2>
      <ResponsiveContainer width="100%" height={160}>
        <PieChart>
          <Pie
            data={data}
            dataKey="amount"
            nameKey="categoryName"
            cx="50%"
            cy="50%"
            innerRadius={48}
            outerRadius={72}
            paddingAngle={2}
          >
            {data.map((entry, i) => (
              <Cell key={entry.categoryId} fill={shades[i]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend */}
      <ul className="mt-3 space-y-1.5 overflow-y-auto flex-1">
        {data.map((entry, i) => (
          <li key={entry.categoryId} className="flex items-center gap-2 text-xs">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
              style={{ backgroundColor: shades[i] }}
            />
            <span className="flex-1 truncate text-foreground">{entry.categoryName}</span>
            <span className="text-muted-foreground shrink-0">{formatCurrency(entry.amount)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
