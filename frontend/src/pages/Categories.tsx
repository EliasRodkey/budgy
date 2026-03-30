import { CategoryCard, CategoryCardSkeleton } from "@/components/categories/CategoryCard";
import { Button } from "@/components/ui/button";
import { useCategoryOverview } from "@/hooks/useCategories";
import { currentMonth, formatMonth } from "@/lib/formatters";
import { AlertCircle, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";

const MONTH = currentMonth();

export default function Categories() {
  const navigate = useNavigate();
  const { data: categories, isLoading, isError, refetch } = useCategoryOverview(MONTH);

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold">Categories</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{formatMonth(MONTH)}</p>
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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <CategoryCardSkeleton key={i} />)
          : categories?.map((spend) => (
              <CategoryCard
                key={spend.categoryId}
                spend={spend}
                onClick={() =>
                  navigate(`/categories/${encodeURIComponent(spend.categoryName)}`)
                }
              />
            ))}
      </div>

      {!isLoading && !isError && categories?.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-12">
          No spending data for this month.
        </p>
      )}
    </div>
  );
}
