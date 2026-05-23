import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/formatters";
import type { AISummary } from "@/types";
import { AlertTriangle, Lightbulb, RefreshCw, Sparkles } from "lucide-react";

interface AISummaryCardProps {
  summary: AISummary | undefined;
  isLoading: boolean;
  isError: boolean;
  onRegenerate: () => void;
  onSummarize?: () => void;
}

function AISkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-7 w-24 rounded-lg" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
      <div className="flex gap-2 mt-2">
        <Skeleton className="h-5 w-28 rounded-full" />
        <Skeleton className="h-5 w-36 rounded-full" />
      </div>
      <Skeleton className="h-4 w-40 mt-2" />
      <div className="space-y-2 pl-3">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
        <Skeleton className="h-3 w-4/6" />
      </div>
    </div>
  );
}

export function AISummaryCard({ summary, isLoading, isError, onRegenerate, onSummarize }: AISummaryCardProps) {
  if (isLoading) return <AISkeleton />;

  if (isError) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 flex flex-col items-center gap-3 text-center">
        <AlertTriangle size={24} className="text-destructive" />
        <p className="text-sm text-muted-foreground">Failed to load AI summary.</p>
        <Button variant="outline" size="sm" onClick={onRegenerate}>
          <RefreshCw size={14} className="mr-1" />
          Retry
        </Button>
      </div>
    );
  }

  if (!summary) {
    if (onSummarize) {
      return (
        <div className="rounded-xl border border-dashed border-border bg-muted/30 p-8 text-center space-y-4">
          <div className="flex justify-center">
            <Sparkles size={32} className="text-muted-foreground/50" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium">AI Summary</p>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto">
              Get an AI-powered recap of your spending this month.
            </p>
          </div>
          <Button size="sm" onClick={onSummarize}>
            Summarize
          </Button>
        </div>
      );
    }
    return null;
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-medium">AI Summary</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Generated {formatDate(summary.generatedAt)}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onRegenerate}>
          <RefreshCw size={14} className="mr-1" />
          Regenerate
        </Button>
      </div>

      <p className="text-sm leading-relaxed">{summary.recap}</p>

      {summary.anomalies.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-amber-600 dark:text-amber-400">
            <AlertTriangle size={13} />
            Anomalies
          </div>
          <div className="flex flex-wrap gap-1.5">
            {summary.anomalies.map((anomaly, i) => (
              <Badge key={i} variant="outline" className="text-xs font-normal h-auto py-1 px-2 whitespace-normal text-left">
                {anomaly}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {summary.suggestions.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <Lightbulb size={13} />
            Suggestions
          </div>
          <ul className="space-y-1.5 pl-1">
            {summary.suggestions.map((s, i) => (
              <li key={i} className="text-sm text-muted-foreground flex gap-2">
                <span className="mt-0.5 shrink-0 text-emerald-500">•</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
