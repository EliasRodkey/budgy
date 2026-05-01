import { CategoryCard, CategoryCardSkeleton } from "@/components/categories/CategoryCard";
import { CategoryDonut } from "@/components/categories/CategoryDonut";
import { DateRangeSelector } from "@/components/categories/DateRangeSelector";
import { Button } from "@/components/ui/button";
import { useCategoryOverview } from "@/hooks/useCategories";
import { CATEGORY_COLORS, NON_SPENDING_CATEGORIES } from "@/lib/categoryColors";
import { formatMonth } from "@/lib/formatters";
import { useDateRangeStore } from "@/store/dateRange";
import { AlertCircle, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Categories() {
  const navigate = useNavigate();
  const { month, year } = useDateRangeStore();
  const { data: categories, isLoading, isError, refetch } = useCategoryOverview(month, year);

  const spending = (categories ?? [])
    .filter((c) => !NON_SPENDING_CATEGORIES.has(c.categoryName))
    .sort((a, b) => b.amount - a.amount);

  const nonSpending = (categories ?? [])
    .filter((c) => NON_SPENDING_CATEGORIES.has(c.categoryName))
    .sort((a, b) => b.amount - a.amount);

  function handleCategoryClick(categoryName: string) {
    navigate(`/categories/${encodeURIComponent(categoryName)}`);
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Categories</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {month !== null
              ? formatMonth(`${year}-${String(month).padStart(2, "0")}`)
              : String(year)}
          </p>
        </div>
        <DateRangeSelector />
      </div>

      {isError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load category overview.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      <CategoryDonut
        categories={categories ?? []}
        isLoading={isLoading}
        onCategoryClick={handleCategoryClick}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading
          ? Array.from({ length: 9 }).map((_, i) => <CategoryCardSkeleton key={i} />)
          : spending.map((spend) => (
              <CategoryCard
                key={spend.categoryId}
                spend={spend}
                color={CATEGORY_COLORS[spend.categoryName]}
                onClick={() => handleCategoryClick(spend.categoryName)}
              />
            ))}
      </div>

      {!isLoading && !isError && nonSpending.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Other
            </span>
            <div className="h-px flex-1 bg-border" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {nonSpending.map((spend) => (
              <CategoryCard
                key={spend.categoryId}
                spend={spend}
                isNonSpending
                onClick={() => handleCategoryClick(spend.categoryName)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
