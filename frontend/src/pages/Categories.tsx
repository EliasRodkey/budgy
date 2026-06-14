import { CategoryCard, CategoryCardSkeleton } from "@/components/categories/CategoryCard";
import { CategoryDonut } from "@/components/categories/CategoryDonut";
import { DateRangeSelector } from "@/components/shared/DateRangeSelector";
import { Button } from "@/components/ui/button";
import { useCategoryOverview } from "@/hooks/useCategories";
import { CATEGORY_COLORS, NON_SPENDING_CATEGORIES } from "@/lib/categoryColors";
import { formatMonth } from "@/lib/formatters";
import { useDateRangeStore } from "@/store/dateRange";
import { AlertCircle, RefreshCw, Upload, PlusCircle, FlaskConical } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useMockMode } from "@/store/mockMode";
import { useQueryClient } from "@tanstack/react-query";

export default function Categories() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toggleMockMode } = useMockMode();
  const { month, year } = useDateRangeStore();
  const { data: categories, isLoading, isError, error, refetch } = useCategoryOverview(month, year);
  const isNoData = isError && (error as (Error & { status?: number }) | null)?.status === 404;

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

      {isNoData && (
        <div className="rounded-xl border border-dashed border-border bg-muted/30 p-8 text-center space-y-4">
          <div className="flex justify-center">
            <Upload size={32} className="text-muted-foreground/50" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium">No transactions yet</p>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto">
              Upload a CSV export from your bank to get started, or try Demo Mode to explore with sample data.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3">
            <Button size="sm" onClick={() => navigate("/transactions")}>
              <Upload size={13} className="mr-1.5" />
              Upload CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/transactions?add=1")}
            >
              <PlusCircle size={13} className="mr-1.5" />
              Add Transaction
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { toggleMockMode(); queryClient.invalidateQueries(); }}
            >
              <FlaskConical size={13} className="mr-1.5" />
              Try Demo Mode
            </Button>
          </div>
        </div>
      )}

      {isError && !isNoData && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load category overview.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      {!isNoData && (
        <CategoryDonut
          categories={categories ?? []}
          isLoading={isLoading}
          onCategoryClick={handleCategoryClick}
        />
      )}

      {!isNoData && (
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
      )}

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
