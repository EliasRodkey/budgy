import { CategoryDonut } from "@/components/categories/CategoryDonut";
import { DeleteConfirmDialog } from "@/components/transactions/DeleteConfirmDialog";
import { EditTransactionModal } from "@/components/transactions/EditTransactionModal";
import { TransactionTable } from "@/components/transactions/TransactionTable";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useTagDetail } from "@/hooks/useTags";
import { useAvailableTags, useDeleteTransaction, useUpdateTransaction } from "@/hooks/useTransactions";
import { CATEGORY_COLORS } from "@/lib/categoryColors";
import { formatCurrency, formatMonth } from "@/lib/formatters";
import type { Transaction } from "@/types";
import {
  AlertCircle,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  DollarSign,
} from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PAGE_SIZE = 10;

function formatYAxisTick(v: number): string {
  if (v >= 1000) return `$${(v / 1000).toFixed(1).replace(/\.0$/, "")}k`;
  return `$${v}`;
}

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
    <div className="rounded-xl border border-border bg-card p-5 space-y-4 h-full">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-52 w-full" />
    </div>
  );
}

function AnalyticCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-2">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-6 w-32" />
    </div>
  );
}

interface AnalyticCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

function AnalyticCard({ icon, label, value }: AnalyticCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-muted-foreground">{icon}</span>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

export default function TagDetail() {
  const { tagName } = useParams<{ tagName: string }>();
  const navigate = useNavigate();
  const decoded = tagName ? decodeURIComponent(tagName) : "";

  const { data, isLoading, isError, error, refetch } = useTagDetail(decoded);

  // Transactions state
  const [page, setPage] = useState(0);
  const [sortByAmount, setSortByAmount] = useState(false);
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [deletingTx, setDeletingTx] = useState<Transaction | null>(null);

  const { mutate: updateTx, isPending: updatePending } = useUpdateTransaction();
  const { mutate: deleteTx, isPending: deletePending } = useDeleteTransaction();
  const { data: availableTags = [] } = useAvailableTags();

  const isNotFound = isError && (error as (Error & { status?: number }) | null)?.status === 404;

  // Sort + paginate transactions
  const sortedTxs = data
    ? [...data.transactions].sort((a, b) =>
        sortByAmount ? Math.abs(b.amount) - Math.abs(a.amount) : 0,
      )
    : [];
  const totalPages = Math.max(1, Math.ceil(sortedTxs.length / PAGE_SIZE));
  const pagedTxs = sortedTxs.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const avgPerTransaction =
    data && data.transactionCount > 0 ? data.totalSpend / data.transactionCount : 0;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Back + header */}
      <div>
        <button
          onClick={() => navigate("/tags")}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
        >
          <ChevronLeft size={15} />
          Tags
        </button>
        <h1 className="text-2xl font-semibold">{decoded}</h1>
        <p className="text-sm text-muted-foreground mt-0.5">All-time spending for this tag</p>
      </div>

      {isError && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
          <AlertCircle size={18} className="text-destructive shrink-0" />
          <p className="text-sm flex-1">
            {isNotFound ? `No data found for tag "${decoded}".` : "Failed to load tag data."}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {/* Row 1: Donut (1/3) + Spend over time (2/3) */}
      <div className="grid grid-cols-3 gap-4 items-stretch">
        <div className="col-span-1">
          <CategoryDonut
            categories={data?.categoryBreakdown ?? []}
            isLoading={isLoading}
            onCategoryClick={(categoryName) => navigate(`/categories/${encodeURIComponent(categoryName)}`)}
          />
        </div>

        <div className="col-span-2">
          {isLoading ? (
            <SpendChartSkeleton />
          ) : data && data.spendOverTime.length > 0 ? (
            <div className="rounded-xl border border-border bg-card p-5 h-full">
              <h2 className="text-sm font-medium text-muted-foreground mb-4">Spend Over Time</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={data.spendOverTime}
                  margin={{ top: 4, right: 8, bottom: 0, left: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis
                    dataKey="month"
                    tickFormatter={formatMonth}
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tickFormatter={formatYAxisTick}
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    width={56}
                    allowDecimals={false}
                  />
                  <Tooltip content={<SpendTooltip />} />
                  <Bar dataKey="amount" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : null}
        </div>
      </div>

      {/* Row 2: Analytics cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => <AnalyticCardSkeleton key={i} />)
        ) : data ? (
          <>
            <AnalyticCard
              icon={<DollarSign size={14} />}
              label="Total spend"
              value={formatCurrency(data.totalSpend)}
            />
            <AnalyticCard
              icon={<CreditCard size={14} />}
              label="Transactions"
              value={String(data.transactionCount)}
            />
            <AnalyticCard
              icon={<DollarSign size={14} />}
              label="Avg per transaction"
              value={formatCurrency(avgPerTransaction)}
            />
          </>
        ) : null}
      </div>

      {/* Row 3: Category breakdown */}
      <div>
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Category breakdown</h2>
        {isLoading ? (
          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="px-4 py-3 flex items-center gap-3">
                <Skeleton className="w-2.5 h-2.5 rounded-full" />
                <Skeleton className="h-3 flex-1" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        ) : data && data.categoryBreakdown.length > 0 ? (
          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {data.categoryBreakdown.map((cat) => {
              const pct = data.totalSpend > 0 ? (cat.amount / data.totalSpend) * 100 : 0;
              const color = CATEGORY_COLORS[cat.categoryName] ?? "#94a3b8";
              return (
                <button
                  key={cat.categoryId}
                  onClick={() => navigate(`/categories/${encodeURIComponent(cat.categoryName)}`)}
                  className="w-full px-4 py-3 flex items-center gap-3 hover:bg-muted/40 transition-colors text-left"
                >
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                  <span className="flex-1 min-w-0">
                    <span className="text-sm font-medium truncate block">{cat.categoryName}</span>
                    <span className="text-xs text-muted-foreground">
                      {cat.transactionCount} transaction{cat.transactionCount !== 1 ? "s" : ""}
                    </span>
                  </span>
                  <div className="w-24 h-1.5 rounded-full bg-muted overflow-hidden shrink-0">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color, opacity: 0.6 }}
                    />
                  </div>
                  <span className="text-sm font-medium tabular-nums shrink-0 w-20 text-right">
                    {formatCurrency(cat.amount)}
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          !isError && (
            <p className="text-sm text-muted-foreground text-center py-12">
              No category data for this tag.
            </p>
          )
        )}
      </div>

      {/* Row 4: Transactions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-muted-foreground">Transactions</h2>
          <button
            onClick={() => {
              setSortByAmount((v) => !v);
              setPage(0);
            }}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowUpDown size={12} />
            {sortByAmount ? "Sort: by amount" : "Sort: newest first"}
          </button>
        </div>

        <TransactionTable
          transactions={pagedTxs}
          isLoading={isLoading}
          onEdit={setEditingTx}
          onDelete={setDeletingTx}
        />

        {!isLoading && sortedTxs.length > 0 && (
          <div className="flex items-center justify-between mt-3">
            <p className="text-xs text-muted-foreground">
              Page {page + 1} of {totalPages}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 0}
              >
                <ChevronLeft size={13} />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages - 1}
              >
                <ChevronRight size={13} />
              </Button>
            </div>
          </div>
        )}

        {!isLoading && sortedTxs.length === 0 && !isError && (
          <p className="text-sm text-muted-foreground text-center py-8">
            No transactions for this tag.
          </p>
        )}
      </div>

      {/* Edit / Delete modals */}
      {editingTx && (
        <EditTransactionModal
          transaction={editingTx}
          isPending={updatePending}
          availableTags={availableTags}
          onClose={() => setEditingTx(null)}
          onSave={(id, updates) => {
            updateTx({ id, updates }, { onSuccess: () => setEditingTx(null) });
          }}
          onDelete={() => { setDeletingTx(editingTx); setEditingTx(null); }}
        />
      )}
      <DeleteConfirmDialog
        transaction={deletingTx}
        isPending={deletePending}
        onClose={() => setDeletingTx(null)}
        onConfirm={(id) => {
          deleteTx(id, { onSuccess: () => setDeletingTx(null) });
        }}
      />
    </div>
  );
}
