import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useTagsOverview } from "@/hooks/useTags";
import { formatCurrency } from "@/lib/formatters";
import { AlertCircle, RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

function TagRowSkeleton() {
  return (
    <div className="px-4 py-3 flex items-center gap-3">
      <Skeleton className="h-4 flex-1" />
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-4 w-20" />
    </div>
  );
}

export default function Tags() {
  const navigate = useNavigate();
  const { data: tags, isLoading, isError, refetch } = useTagsOverview();
  const [search, setSearch] = useState("");

  const filtered = (tags ?? []).filter((tag) =>
    tag.tagName.toLowerCase().includes(search.trim().toLowerCase()),
  );

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold">Tags</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Track spending for trips, projects, or other ad-hoc groupings.
        </p>
      </div>

      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter tags…"
          className="w-full h-9 rounded-md border border-input bg-background pl-8 pr-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>

      {isError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load tags.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      {isLoading ? (
        <div className="rounded-xl border border-border bg-card divide-y divide-border">
          {Array.from({ length: 5 }).map((_, i) => <TagRowSkeleton key={i} />)}
        </div>
      ) : !isError && filtered.length > 0 ? (
        <div className="rounded-xl border border-border bg-card divide-y divide-border">
          {filtered.map((tag) => (
            <button
              key={tag.tagName}
              onClick={() => navigate(`/tags/${encodeURIComponent(tag.tagName)}`)}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-muted/40 transition-colors text-left"
            >
              <span className="flex-1 min-w-0">
                <span className="text-sm font-medium truncate block">{tag.tagName}</span>
                <span className="text-xs text-muted-foreground">
                  {tag.transactionCount} transaction{tag.transactionCount !== 1 ? "s" : ""}
                </span>
              </span>
              <span className="text-sm font-medium tabular-nums shrink-0">
                {formatCurrency(tag.totalSpend)}
              </span>
            </button>
          ))}
        </div>
      ) : !isError && (tags ?? []).length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-12">
          No tags yet. Add tags to transactions to start tracking them here.
        </p>
      ) : !isError ? (
        <p className="text-sm text-muted-foreground text-center py-12">
          No tags match "{search}".
        </p>
      ) : null}
    </div>
  );
}
