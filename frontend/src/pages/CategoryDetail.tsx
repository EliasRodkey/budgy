import { DetailCategoryDonut } from "@/components/categories/DetailCategoryDonut";
import { DeleteConfirmDialog } from "@/components/transactions/DeleteConfirmDialog";
import { EditTransactionModal } from "@/components/transactions/EditTransactionModal";
import { TransactionTable } from "@/components/transactions/TransactionTable";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCategoryDetail } from "@/hooks/useCategories";
import { useAvailableTags, useDeleteTransaction, useUpdateTransaction } from "@/hooks/useTransactions";
import { CATEGORY_COLORS } from "@/lib/categoryColors";
import { currentMonth, formatCurrency, formatMonth } from "@/lib/formatters";
import type { Transaction } from "@/types";
import {
  AlertCircle,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  DollarSign,
  ExternalLink,
  RefreshCw,
  Target,
  TrendingDown,
  Wallet,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PAGE_SIZE = 10;

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
  value: string | React.ReactNode;
  accent?: boolean;
}

function AnalyticCard({ icon, label, value, accent }: AnalyticCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-muted-foreground">{icon}</span>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${accent ? "text-destructive" : ""}`}>{value}</p>
    </div>
  );
}

export default function CategoryDetail() {
  const { primaryCategory } = useParams<{ primaryCategory: string }>();
  const navigate = useNavigate();
  const decoded = primaryCategory ? decodeURIComponent(primaryCategory) : "";

  const { data, isLoading, isError, refetch } = useCategoryDetail(decoded);

  // Transactions state
  const [page, setPage] = useState(0);
  const [sortByAmount, setSortByAmount] = useState(false);
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [deletingTx, setDeletingTx] = useState<Transaction | null>(null);

  const { mutate: updateTx, isPending: updatePending } = useUpdateTransaction();
  const { mutate: deleteTx, isPending: deletePending } = useDeleteTransaction();
  const { data: availableTags = [] } = useAvailableTags();

  const baseColor = CATEGORY_COLORS[decoded] ?? "#94a3b8";

  // Sort + paginate transactions
  const sortedTxs = data
    ? [...data.currentMonthTransactions].sort((a, b) =>
        sortByAmount ? Math.abs(b.amount) - Math.abs(a.amount) : 0,
      )
    : [];
  const totalPages = Math.max(1, Math.ceil(sortedTxs.length / PAGE_SIZE));
  const pagedTxs = sortedTxs.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const remaining =
    data?.budget != null ? data.budget - data.currentMonthTotal : null;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
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
        <p className="text-sm text-muted-foreground mt-0.5">{formatMonth(currentMonth())}</p>
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

      {/* Row 1: Donut (1/3) + Spend over time (2/3) */}
      <div className="grid grid-cols-3 gap-4 items-stretch">
        {/* Donut */}
        <div className="col-span-1">
          <DetailCategoryDonut
            subcategories={data?.currentMonthSubcategories ?? []}
            baseColor={baseColor}
            isLoading={isLoading}
          />
        </div>

        {/* Spend over time */}
        <div className="col-span-2">
          {isLoading ? (
            <SpendChartSkeleton />
          ) : data && data.spendOverTime.length > 0 ? (
            <div className="rounded-xl border border-border bg-card p-5 h-full">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium text-muted-foreground">Spend Over Time</h2>
                {data.budget === null && (
                  <span className="text-xs text-muted-foreground italic">No budget set</span>
                )}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
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
                  {data.budget !== null && (
                    <ReferenceLine
                      y={data.budget}
                      stroke={baseColor}
                      strokeDasharray="4 4"
                      strokeWidth={1.5}
                      strokeOpacity={0.7}
                      label={{
                        value: `Budget: ${formatCurrency(data.budget)}`,
                        position: "insideTopRight",
                        fontSize: 10,
                        fill: baseColor,
                        opacity: 0.8,
                      }}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : null}
        </div>
      </div>

      {/* Row 2: Analytics cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <AnalyticCardSkeleton key={i} />)
        ) : data ? (
          <>
            <AnalyticCard
              icon={<TrendingDown size={14} />}
              label="Avg spend (this year)"
              value={formatCurrency(data.yearAvgSpend)}
            />
            <AnalyticCard
              icon={<Target size={14} />}
              label="Monthly budget"
              value={
                data.budget !== null ? (
                  formatCurrency(data.budget)
                ) : (
                  <span className="text-sm font-normal text-muted-foreground">No budget set</span>
                )
              }
            />
            <AnalyticCard
              icon={<DollarSign size={14} />}
              label="Total spend (this month)"
              value={formatCurrency(data.currentMonthTotal)}
            />
            <AnalyticCard
              icon={<Wallet size={14} />}
              label="Remaining budget"
              accent={remaining !== null && remaining < 0}
              value={
                remaining !== null ? (
                  formatCurrency(remaining)
                ) : (
                  <span className="text-sm font-normal text-muted-foreground">No budget set</span>
                )
              }
            />
            <AnalyticCard
              icon={<CreditCard size={14} />}
              label="Transactions (this month)"
              value={String(data.currentMonthTxCount)}
            />
          </>
        ) : null}
      </div>

      {/* Row 3: Detailed categories compact list */}
      <div>
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Subcategories</h2>
        {isLoading ? (
          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="px-4 py-3 flex items-center gap-3">
                <Skeleton className="w-2.5 h-2.5 rounded-full" />
                <Skeleton className="h-3 flex-1" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        ) : data && data.currentMonthSubcategories.length > 0 ? (
          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {data.currentMonthSubcategories.map((sub) => {
              const pct =
                data.currentMonthTotal > 0
                  ? (sub.amount / data.currentMonthTotal) * 100
                  : 0;
              return (
                <button
                  key={sub.categoryId}
                  onClick={() =>
                    navigate(
                      `/categories/${encodeURIComponent(decoded)}/${encodeURIComponent(sub.categoryName)}`,
                    )
                  }
                  className="w-full px-4 py-3 flex items-center gap-3 hover:bg-muted/40 transition-colors text-left"
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: baseColor }}
                  />
                  <span className="flex-1 min-w-0">
                    <span className="text-sm font-medium truncate block">{sub.categoryName}</span>
                    <span className="text-xs text-muted-foreground">
                      {sub.transactionCount} transaction{sub.transactionCount !== 1 ? "s" : ""}
                    </span>
                  </span>
                  {/* Proportional bar */}
                  <div className="w-24 h-1.5 rounded-full bg-muted overflow-hidden shrink-0">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: baseColor, opacity: 0.6 }}
                    />
                  </div>
                  <span className="text-sm font-medium tabular-nums shrink-0 w-20 text-right">
                    {formatCurrency(sub.amount)}
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          !isError && (
            <p className="text-sm text-muted-foreground text-center py-12">
              No transactions this month.
            </p>
          )
        )}
      </div>

      {/* Row 4: Transactions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-muted-foreground">Transactions this month</h2>
          <div className="flex items-center gap-3">
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
            <Link
              to="/transactions"
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              View all
              <ExternalLink size={11} />
            </Link>
          </div>
        </div>

        <TransactionTable
          transactions={pagedTxs}
          isLoading={isLoading}
          onEdit={setEditingTx}
          onDelete={setDeletingTx}
        />

        {/* Pagination */}
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
            No transactions this month.
          </p>
        )}
      </div>

      {/* Edit / Delete modals */}
      <EditTransactionModal
        transaction={editingTx}
        isPending={updatePending}
        availableTags={availableTags}
        onClose={() => setEditingTx(null)}
        onSave={(id, updates) => {
          updateTx({ id, updates }, { onSuccess: () => setEditingTx(null) });
        }}
      />
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
