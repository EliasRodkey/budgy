import { CategoryCard, CategoryCardSkeleton } from "@/components/categories/CategoryCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCategoryDetail } from "@/hooks/useCategories";
import { formatCurrency, formatMonth } from "@/lib/formatters";
import { AlertCircle, ChevronLeft, RefreshCw } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ChartTooltipProps {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}

function SpendTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm">
      <p className="font-medium">{label ? formatMonth(label) : ""}</p>
      <p className="text-muted-foreground">{formatCurrency(payload[0].value)}</p>
    </div>
  );
}

function SpendChartSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-4">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-52 w-full" />
    </div>
  );
}

export default function CategoryDetail() {
  const { primaryCategory } = useParams<{ primaryCategory: string }>();
  const navigate = useNavigate();
  const decoded = primaryCategory ? decodeURIComponent(primaryCategory) : "";

  const { data, isLoading, isError, refetch } = useCategoryDetail(decoded);

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Back + header */}
      <div>
        <button
          onClick={() => navigate("/categories")}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
        >
          <ChevronLeft size={15} />
          Categories
        </button>
        <h1 className="text-2xl font-semibold">{decoded}</h1>
      </div>

      {isError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load category data.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      {/* Spend-over-time chart */}
      {isLoading ? (
        <SpendChartSkeleton />
      ) : data && data.spendOverTime.length > 0 ? (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">Spend Over Time</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data.spendOverTime} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="month"
                tickFormatter={formatMonth}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tickFormatter={(v) => `$${v}`}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={56}
              />
              <Tooltip content={<SpendTooltip />} />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="var(--primary)"
                strokeWidth={2}
                dot={{ r: 4, fill: "var(--primary)" }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      {/* Subcategory cards */}
      <div>
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Subcategories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => <CategoryCardSkeleton key={i} />)
            : data?.subcategories.map((sub) => (
                <CategoryCard
                  key={sub.categoryId}
                  spend={sub}
                  onClick={() =>
                    navigate(
                      `/categories/${encodeURIComponent(decoded)}/${encodeURIComponent(sub.categoryName)}`,
                    )
                  }
                />
              ))}
        </div>

        {!isLoading && !isError && data?.subcategories.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-12">
            No transactions for this category.
          </p>
        )}
      </div>
    </div>
  );
}
