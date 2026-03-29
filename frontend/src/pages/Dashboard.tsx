import { AISummaryCard } from "@/components/dashboard/AISummaryCard";
import { FlaggedTransactionsList } from "@/components/dashboard/FlaggedTransactionsList";
import { SpendingDonut } from "@/components/dashboard/SpendingDonut";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { Button } from "@/components/ui/button";
import { useAISummary } from "@/hooks/useAISummary";
import { useAssignCategory, useFlaggedTransactions } from "@/hooks/useFlaggedTransactions";
import { useSummary } from "@/hooks/useSummary";
import { currentMonth, formatMonth } from "@/lib/formatters";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, RefreshCw } from "lucide-react";

const MONTH = currentMonth();

export default function Dashboard() {
  const queryClient = useQueryClient();

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useSummary(MONTH);

  const {
    data: aiSummary,
    isLoading: aiLoading,
    isError: aiError,
    refetch: refetchAI,
  } = useAISummary(MONTH);

  const {
    data: flagged,
    isLoading: flaggedLoading,
    isError: flaggedError,
  } = useFlaggedTransactions();

  const { mutate: assign, isPending: assignPending } = useAssignCategory();

  function handleRegenerate() {
    queryClient.removeQueries({ queryKey: ["aiSummary", MONTH] });
    refetchAI();
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{formatMonth(MONTH)}</p>
      </div>

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

      {/* Financial snapshot cards */}
      <SummaryCards summary={summary} isLoading={summaryLoading} />

      {/* Donut chart */}
      <SpendingDonut summary={summary} isLoading={summaryLoading} />

      {/* AI Summary */}
      <AISummaryCard
        summary={aiSummary}
        isLoading={aiLoading}
        isError={aiError}
        onRegenerate={handleRegenerate}
      />

      {/* Flagged transactions */}
      <FlaggedTransactionsList
        transactions={flagged}
        isLoading={flaggedLoading}
        isError={flaggedError}
        onAssign={(transactionId, primaryCategory, detailedCategory) =>
          assign({ transactionId, primaryCategory, detailedCategory })
        }
        isPending={assignPending}
      />
    </div>
  );
}
