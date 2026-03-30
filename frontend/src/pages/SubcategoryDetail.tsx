import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSubcategoryDetail } from "@/hooks/useCategories";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { AlertCircle, ChevronLeft, RefreshCw } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function MetricCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-2">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-6 w-20" />
    </div>
  );
}

export default function SubcategoryDetail() {
  const { primaryCategory, detailedCategory } = useParams<{
    primaryCategory: string;
    detailedCategory: string;
  }>();
  const navigate = useNavigate();

  const decodedPrimary = primaryCategory ? decodeURIComponent(primaryCategory) : "";
  const decodedDetailed = detailedCategory ? decodeURIComponent(detailedCategory) : "";

  const { data, isLoading, isError, refetch } = useSubcategoryDetail(
    decodedPrimary,
    decodedDetailed,
  );

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Back + header */}
      <div>
        <button
          onClick={() => navigate(`/categories/${encodeURIComponent(decodedPrimary)}`)}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
        >
          <ChevronLeft size={15} />
          {decodedPrimary}
        </button>
        <h1 className="text-2xl font-semibold">{decodedDetailed}</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{decodedPrimary}</p>
      </div>

      {isError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load subcategory data.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : data ? (
          <>
            <MetricCard label="Transactions" value={String(data.transactionCount)} />
            <MetricCard
              label="Average transaction"
              value={formatCurrency(data.avgTransactionSize)}
            />
            <MetricCard
              label="Total spend"
              value={formatCurrency(
                data.transactions.reduce((s, t) => s + Math.abs(t.amount), 0),
              )}
            />
          </>
        ) : null}
      </div>

      {/* Top vendors */}
      {(isLoading || (data && data.topVendors.length > 0)) && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">Top Vendors</h2>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-20" />
                </div>
              ))}
            </div>
          ) : (
            <ul className="space-y-2">
              {data?.topVendors.map((vendor) => (
                <li
                  key={vendor.name}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="font-medium">{vendor.name}</span>
                  <span className="text-muted-foreground tabular-nums">
                    {formatCurrency(vendor.amount)}{" "}
                    <span className="text-xs">
                      ({vendor.count} txn{vendor.count !== 1 ? "s" : ""})
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Transaction list */}
      <div>
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Transactions</h2>

        {isLoading ? (
          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="p-4 flex items-center justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <Skeleton className="h-4 w-36" />
                  <Skeleton className="h-3 w-20" />
                </div>
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        ) : data && data.transactions.length > 0 ? (
          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {data.transactions.map((tx) => (
              <div
                key={tx.id}
                className="p-4 flex items-center justify-between gap-4"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{tx.merchant}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(tx.date)}</p>
                  {tx.description && tx.description !== tx.merchant && (
                    <p className="text-xs text-muted-foreground truncate">{tx.description}</p>
                  )}
                </div>
                <p className="text-sm font-semibold tabular-nums shrink-0 text-destructive">
                  {formatCurrency(tx.amount)}
                </p>
              </div>
            ))}
          </div>
        ) : !isLoading && !isError ? (
          <p className="text-sm text-muted-foreground text-center py-12">
            No transactions for this subcategory.
          </p>
        ) : null}
      </div>
    </div>
  );
}
