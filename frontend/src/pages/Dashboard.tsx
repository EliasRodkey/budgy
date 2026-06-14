import { AISummaryCard } from "@/components/dashboard/AISummaryCard";
import { BudgetGauge } from "@/components/dashboard/BudgetGauge";
import { FlaggedTransactionsList } from "@/components/dashboard/FlaggedTransactionsList";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { CategoryDonut } from "@/components/categories/CategoryDonut";
import { DateRangeSelector } from "@/components/shared/DateRangeSelector";
import { DeleteConfirmDialog } from "@/components/transactions/DeleteConfirmDialog";
import { EditTransactionModal } from "@/components/transactions/EditTransactionModal";
import { Button } from "@/components/ui/button";
import { useAISummary } from "@/hooks/useAISummary";
import { useFlaggedTransactions } from "@/hooks/useFlaggedTransactions";
import { useUpdateTransaction, useDeleteTransaction, useAvailableTags } from "@/hooks/useTransactions";
import { usePeriodSummary, useAvailableYears, useDirtyMonths } from "@/hooks/useSummary";
import { formatMonth } from "@/lib/formatters";
import { recomputeSummaries } from "@/api/summary";
import { useDateRangeStore } from "@/store/dateRange";
import { useMockMode } from "@/store/mockMode";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, FlaskConical, PlusCircle, RefreshCw, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Transaction } from "@/types";

export default function Dashboard() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { isMockMode, toggleMockMode } = useMockMode();
  const [recomputing, setRecomputing] = useState(false);
  const recomputeStarted = useRef(false);
  const [editTarget, setEditTarget] = useState<Transaction | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Transaction | null>(null);
  const [aiEnabled, setAiEnabled] = useState(false);

  const { month, year } = useDateRangeStore();
  const period = month !== null ? `${year}-${String(month).padStart(2, "0")}` : String(year);

  const { data: dirtyData } = useDirtyMonths();
  const { data: availableYears = [] } = useAvailableYears();

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = usePeriodSummary(month, year);

  useEffect(() => {
    if (dirtyData?.dirty && !recomputeStarted.current) {
      recomputeStarted.current = true;
      setRecomputing(true);
      recomputeSummaries()
        .then(() => refetchSummary())
        .finally(() => {
          setRecomputing(false);
          queryClient.invalidateQueries({ queryKey: ["summaries", "dirty"] });
        });
    }
  }, [dirtyData, refetchSummary, queryClient]);

  const {
    data: aiSummary,
    isLoading: aiLoading,
    isError: aiError,
    refetch: refetchAI,
  } = useAISummary(period, aiEnabled);

  const {
    data: flagged,
    isLoading: flaggedLoading,
    isError: flaggedError,
  } = useFlaggedTransactions();

  const { mutate: updateTx, isPending: updatePending } = useUpdateTransaction();
  const { mutate: deleteTx, isPending: deletePending } = useDeleteTransaction();
  const { data: availableTags = [] } = useAvailableTags();

  function handleRegenerate() {
    queryClient.removeQueries({ queryKey: ["aiSummary", period] });
    refetchAI();
  }

  function handleSave(id: string, updates: Partial<Transaction>) {
    updateTx({ id, updates }, {
      onSuccess: () => {
        setEditTarget(null);
        queryClient.invalidateQueries({ queryKey: ["flaggedTransactions"] });
      },
    });
  }

  function handleDelete(id: string) {
    deleteTx(id, {
      onSuccess: () => {
        setDeleteTarget(null);
        queryClient.invalidateQueries({ queryKey: ["flaggedTransactions"] });
      },
    });
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {month !== null ? formatMonth(period) : String(year)}
          </p>
        </div>
        <DateRangeSelector />
      </div>

      {/* Empty state — no data anywhere and not in demo mode */}
      {!summaryLoading && !summaryError && !isMockMode && !summary && availableYears.length === 0 && (
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

      {/* Empty state — no data for the selected period, but data exists elsewhere */}
      {!summaryLoading && !summaryError && !summary && (isMockMode || availableYears.length > 0) && (
        <div className="rounded-xl border border-dashed border-border bg-muted/30 p-8 text-center">
          <p className="text-sm text-muted-foreground">No data for this period.</p>
        </div>
      )}

      {/* Summary error state */}
      {summaryError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">Failed to load monthly summary.</p>
          <Button variant="outline" size="sm" onClick={() => refetchSummary()}>
            <RefreshCw size={13} className="mr-1" />
            Retry
          </Button>
        </div>
      )}

      {(summaryLoading || summary) && recomputing && (
        <p className="text-xs text-muted-foreground flex items-center gap-1.5">
          <RefreshCw size={11} className="animate-spin" />
          Updating summaries…
        </p>
      )}

      {(summaryLoading || summary) && (
        <>
          {/* Financial snapshot cards */}
          <SummaryCards summary={summary} isLoading={summaryLoading} />

          {/* Budget gauge + donut chart */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <BudgetGauge byCategory={summary?.byCategory ?? []} isLoading={summaryLoading} />
            <CategoryDonut
              categories={summary?.byCategory ?? []}
              isLoading={summaryLoading}
              onCategoryClick={(name) => navigate(`/categories/${encodeURIComponent(name)}`)}
              height={260}
              innerRadius={60}
              outerRadius={100}
            />
          </div>

          {/* AI Summary */}
          <AISummaryCard
            summary={aiSummary}
            isLoading={aiLoading}
            isError={aiError}
            onRegenerate={handleRegenerate}
            onSummarize={!aiEnabled ? () => setAiEnabled(true) : undefined}
          />

          {/* Flagged transactions */}
          <FlaggedTransactionsList
            transactions={flagged}
            isLoading={flaggedLoading}
            isError={flaggedError}
            onEdit={setEditTarget}
          />
        </>
      )}

      {/* Edit modal — opened from flagged list */}
      {editTarget && (
        <EditTransactionModal
          transaction={editTarget}
          isPending={updatePending}
          availableTags={availableTags}
          onSave={handleSave}
          onClose={() => setEditTarget(null)}
          onDelete={() => { setDeleteTarget(editTarget); setEditTarget(null); }}
        />
      )}
      <DeleteConfirmDialog
        transaction={deleteTarget}
        isPending={deletePending}
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
