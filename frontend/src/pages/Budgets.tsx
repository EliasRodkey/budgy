import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CATEGORY_MAPPING } from "@/constants/categories";
import {
  useBudgetAssignments,
  useBudgets,
  useCreateBudget,
  useCreateBudgetAssignment,
  useDeleteBudget,
  useDeleteBudgetAssignment,
} from "@/hooks/useBudgets";
import { getEffectiveBudget } from "@/lib/budget";
import { currentMonth, formatCurrency, formatDate, formatMonth } from "@/lib/formatters";
import type { Budget, BudgetAssignment } from "@/types";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  CalendarCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  PlusCircle,
  RefreshCw,
  Trash2,
  Wallet,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

// ─── Primary spending categories (excludes flow-through categories) ────────────

const SPENDING_CATEGORIES = Object.keys(CATEGORY_MAPPING).filter(
  (c) => !["Income", "Transfers", "Debt payments", "Investments", "Bank fees"].includes(c),
);

// ─── Zod schemas ──────────────────────────────────────────────────────────────

const budgetSchema = z.object({
  categoryLimits: z.record(
    z.string(),
    z.number({ error: "Must be a number" }).min(0, "Must be ≥ 0"),
  ),
  incomeEstimate: z.number({ error: "Must be a number" }).min(0, "Must be ≥ 0"),
});

type BudgetFormValues = z.infer<typeof budgetSchema>;

const assignmentSchema = z.object({
  budgetId: z.string().min(1, "Select a budget"),
  effectiveFrom: z
    .string()
    .regex(/^\d{4}-\d{2}$/, "Must be YYYY-MM format"),
  note: z.string().max(200, "Max 200 characters").optional(),
});

type AssignmentFormValues = z.infer<typeof assignmentSchema>;

// ─── Skeleton components ──────────────────────────────────────────────────────

function ActiveBudgetSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-3 w-40" />
    </div>
  );
}

function BudgetCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <Skeleton className="h-5 w-32" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  );
}

// ─── Error card ───────────────────────────────────────────────────────────────

function ErrorCard({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5 flex items-center gap-3">
      <AlertCircle size={18} className="text-destructive shrink-0" />
      <p className="text-sm flex-1">{message}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCw size={13} className="mr-1" />
        Retry
      </Button>
    </div>
  );
}

// ─── Active budget card ───────────────────────────────────────────────────────

interface ActiveBudgetCardProps {
  budgets: Budget[];
  assignments: BudgetAssignment[];
}

function ActiveBudgetCard({ budgets, assignments }: ActiveBudgetCardProps) {
  const month = currentMonth();
  const active = getEffectiveBudget(assignments, month);
  const budget = active ? budgets.find((b) => b.id === active.budgetId) : null;

  if (!active || !budget) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-muted/30 p-5 flex items-center gap-3">
        <CalendarCheck size={18} className="text-muted-foreground shrink-0" />
        <p className="text-sm text-muted-foreground">
          No budget is currently active. Assign a budget below to get started.
        </p>
      </div>
    );
  }

  const limitTotal = Object.values(budget.categoryLimits).reduce((s, v) => s + v, 0);

  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 space-y-2">
      <div className="flex items-center gap-2 text-primary">
        <CheckCircle2 size={16} className="shrink-0" />
        <span className="text-xs font-medium uppercase tracking-wide">Active budget</span>
      </div>
      <div className="flex items-baseline gap-3 flex-wrap">
        <span className="text-lg font-semibold">
          Created {formatDate(budget.dateCreated)}
        </span>
        <span className="text-sm text-muted-foreground">
          assigned from {formatMonth(active.effectiveFrom)}
        </span>
      </div>
      <div className="flex gap-6 text-sm text-muted-foreground pt-1">
        <span>
          <span className="font-medium text-foreground">{formatCurrency(limitTotal)}</span>{" "}
          total limits
        </span>
        <span>
          Net:{" "}
          <span
            className={
              budget.netGainOrLoss >= 0
                ? "font-medium text-green-600 dark:text-green-400"
                : "font-medium text-destructive"
            }
          >
            {formatCurrency(budget.netGainOrLoss)}
          </span>
        </span>
      </div>
      {active.note && (
        <p className="text-xs text-muted-foreground border-t border-border/50 pt-2 mt-2">
          {active.note}
        </p>
      )}
    </div>
  );
}

// ─── Budget card (in list) ────────────────────────────────────────────────────

interface BudgetCardProps {
  budget: Budget;
  isActive: boolean;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

function BudgetCard({ budget, isActive, onDelete, isDeleting }: BudgetCardProps) {
  const [expanded, setExpanded] = useState(false);
  const limits = Object.entries(budget.categoryLimits);

  return (
    <div
      className={`rounded-xl border bg-card p-5 space-y-3 ${
        isActive ? "border-primary/40" : "border-border"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Wallet size={15} className="text-muted-foreground" />
            <span className="text-sm font-medium">
              Created {formatDate(budget.dateCreated)}
            </span>
            {isActive && (
              <span className="text-[10px] font-semibold uppercase tracking-wide text-primary bg-primary/10 rounded px-1.5 py-0.5">
                Active
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {limits.length} categor{limits.length === 1 ? "y" : "ies"} ·{" "}
            Net:{" "}
            <span
              className={
                budget.netGainOrLoss >= 0
                  ? "text-green-600 dark:text-green-400"
                  : "text-destructive"
              }
            >
              {formatCurrency(budget.netGainOrLoss)}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-muted-foreground"
            onClick={() => setExpanded((e) => !e)}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-destructive hover:text-destructive"
            onClick={() => onDelete(budget.id)}
            disabled={isDeleting}
          >
            <Trash2 size={14} />
          </Button>
        </div>
      </div>

      {expanded && (
        <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 border-t border-border pt-3 text-sm">
          {limits.map(([category, limit]) => (
            <div key={category} className="flex justify-between gap-2">
              <span className="text-muted-foreground truncate">{category}</span>
              <span className="font-medium tabular-nums">{formatCurrency(limit)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Create budget form ───────────────────────────────────────────────────────

interface CreateBudgetFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

function CreateBudgetForm({ onSuccess, onCancel }: CreateBudgetFormProps) {
  const { mutate, isPending } = useCreateBudget();

  const defaultValues: BudgetFormValues = {
    categoryLimits: Object.fromEntries(SPENDING_CATEGORIES.map((c) => [c, 0])),
    incomeEstimate: 0,
  };

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<BudgetFormValues>({
    resolver: zodResolver(budgetSchema),
    defaultValues,
  });

  const watched = watch();
  const totalLimits = SPENDING_CATEGORIES.reduce(
    (sum, c) => sum + (Number(watched.categoryLimits?.[c]) || 0),
    0,
  );
  const net = (Number(watched.incomeEstimate) || 0) - totalLimits;

  function onSubmit(values: BudgetFormValues) {
    const income = Number(values.incomeEstimate) || 0;
    const limits: Record<string, number> = {};
    for (const [cat, val] of Object.entries(values.categoryLimits)) {
      const n = Number(val);
      if (n > 0) limits[cat] = n;
    }
    const limitSum = Object.values(limits).reduce((s, v) => s + v, 0);
    mutate(
      { categoryLimits: limits, netGainOrLoss: income - limitSum },
      { onSuccess },
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div className="space-y-1">
        <label className="text-sm font-medium">Monthly income estimate</label>
        <input
          type="number"
          min="0"
          step="0.01"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("incomeEstimate", { valueAsNumber: true })}
        />
        {errors.incomeEstimate && (
          <p className="text-xs text-destructive">{errors.incomeEstimate.message}</p>
        )}
      </div>

      <div>
        <p className="text-sm font-medium mb-3">Category spending limits</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
          {SPENDING_CATEGORIES.map((category) => (
            <div key={category} className="space-y-1">
              <label className="text-xs text-muted-foreground">{category}</label>
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="0"
                className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                {...register(`categoryLimits.${category}`, { valueAsNumber: true })}
              />
              {errors.categoryLimits?.[category] && (
                <p className="text-xs text-destructive">
                  {errors.categoryLimits[category]?.message}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Live net calculation */}
      <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          <span className="text-foreground font-medium">{formatCurrency(Number(watched.incomeEstimate) || 0)}</span>
          {" income − "}
          <span className="text-foreground font-medium">{formatCurrency(totalLimits)}</span>
          {" limits"}
        </div>
        <div className="text-sm font-semibold">
          Net:{" "}
          <span className={net >= 0 ? "text-green-600 dark:text-green-400" : "text-destructive"}>
            {formatCurrency(net)}
          </span>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Saving…" : "Create budget"}
        </Button>
      </div>
    </form>
  );
}

// ─── Budget assignment form ───────────────────────────────────────────────────

interface AssignBudgetFormProps {
  budgets: Budget[];
  onSuccess: () => void;
  onCancel: () => void;
}

function AssignBudgetForm({ budgets, onSuccess, onCancel }: AssignBudgetFormProps) {
  const { mutate, isPending } = useCreateBudgetAssignment();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AssignmentFormValues>({
    resolver: zodResolver(assignmentSchema),
    defaultValues: { budgetId: "", effectiveFrom: currentMonth(), note: "" },
  });

  function onSubmit(values: AssignmentFormValues) {
    mutate(
      {
        budgetId: values.budgetId,
        effectiveFrom: values.effectiveFrom,
        note: values.note || null,
      },
      { onSuccess },
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1">
        <label className="text-sm font-medium">Budget</label>
        <select
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("budgetId")}
        >
          <option value="">Select a budget…</option>
          {budgets.map((b) => (
            <option key={b.id} value={b.id}>
              Created {formatDate(b.dateCreated)} — Net {formatCurrency(b.netGainOrLoss)}
            </option>
          ))}
        </select>
        {errors.budgetId && (
          <p className="text-xs text-destructive">{errors.budgetId.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium">Effective from (YYYY-MM)</label>
        <input
          type="text"
          placeholder="2025-01"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("effectiveFrom")}
        />
        {errors.effectiveFrom && (
          <p className="text-xs text-destructive">{errors.effectiveFrom.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium">Note (optional)</label>
        <input
          type="text"
          placeholder="e.g. New Year revision"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("note")}
        />
        {errors.note && (
          <p className="text-xs text-destructive">{errors.note.message}</p>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Assigning…" : "Assign budget"}
        </Button>
      </div>
    </form>
  );
}

// ─── Assignment history list ──────────────────────────────────────────────────

interface AssignmentHistoryProps {
  assignments: BudgetAssignment[];
  budgets: Budget[];
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

function AssignmentHistory({
  assignments,
  budgets,
  onDelete,
  isDeleting,
}: AssignmentHistoryProps) {
  const sorted = [...assignments].sort((a, b) =>
    b.effectiveFrom.localeCompare(a.effectiveFrom),
  );

  if (sorted.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-2">
        No assignments yet. Assign a budget above to start.
      </p>
    );
  }

  return (
    <div className="divide-y divide-border rounded-xl border border-border overflow-hidden">
      {sorted.map((a) => {
        const budget = budgets.find((b) => b.id === a.budgetId);
        return (
          <div key={a.id} className="flex items-center justify-between gap-4 px-4 py-3 bg-card">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium">{formatMonth(a.effectiveFrom)}</span>
                {budget && (
                  <span className="text-xs text-muted-foreground">
                    Budget created {formatDate(budget.dateCreated)} · Net{" "}
                    <span
                      className={
                        budget.netGainOrLoss >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-destructive"
                      }
                    >
                      {formatCurrency(budget.netGainOrLoss)}
                    </span>
                  </span>
                )}
              </div>
              {a.note && (
                <p className="text-xs text-muted-foreground mt-0.5 truncate">{a.note}</p>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-destructive hover:text-destructive shrink-0"
              onClick={() => onDelete(a.id)}
              disabled={isDeleting}
            >
              <Trash2 size={14} />
            </Button>
          </div>
        );
      })}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Budgets() {
  const {
    data: budgets,
    isLoading: loadingBudgets,
    isError: errorBudgets,
    refetch: refetchBudgets,
  } = useBudgets();

  const {
    data: assignments,
    isLoading: loadingAssignments,
    isError: errorAssignments,
    refetch: refetchAssignments,
  } = useBudgetAssignments();

  const { mutate: deleteBudget, isPending: deletingBudget } = useDeleteBudget();
  const { mutate: deleteAssignment, isPending: deletingAssignment } =
    useDeleteBudgetAssignment();

  const [showCreateBudget, setShowCreateBudget] = useState(false);
  const [showAssignForm, setShowAssignForm] = useState(false);

  const isLoading = loadingBudgets || loadingAssignments;
  const isError = errorBudgets || errorAssignments;

  const activeAssignment =
    budgets && assignments
      ? getEffectiveBudget(assignments, currentMonth())
      : null;

  return (
    <div className="p-6 space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold">Budgets</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage budgets and track which one is active each month.
        </p>
      </div>

      {isError && (
        <ErrorCard
          message="Failed to load budget data."
          onRetry={() => {
            refetchBudgets();
            refetchAssignments();
          }}
        />
      )}

      {/* ── Active budget ── */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold">Active budget</h2>
        {isLoading ? (
          <ActiveBudgetSkeleton />
        ) : (
          <ActiveBudgetCard
            budgets={budgets ?? []}
            assignments={assignments ?? []}
          />
        )}
      </section>

      {/* ── Budget list ── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Budgets</h2>
          {!showCreateBudget && (
            <Button size="sm" onClick={() => setShowCreateBudget(true)}>
              <PlusCircle size={14} className="mr-1.5" />
              New budget
            </Button>
          )}
        </div>

        {showCreateBudget && (
          <div className="rounded-xl border border-border bg-card p-5">
            <p className="text-sm font-medium mb-4">Create new budget</p>
            <CreateBudgetForm
              onSuccess={() => setShowCreateBudget(false)}
              onCancel={() => setShowCreateBudget(false)}
            />
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            <BudgetCardSkeleton />
            <BudgetCardSkeleton />
          </div>
        ) : (budgets ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground py-2">
            No budgets yet. Create one above.
          </p>
        ) : (
          <div className="space-y-3">
            {(budgets ?? []).map((b) => (
              <BudgetCard
                key={b.id}
                budget={b}
                isActive={activeAssignment?.budgetId === b.id}
                onDelete={deleteBudget}
                isDeleting={deletingBudget}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── Assignment ── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Assignment history</h2>
          {!showAssignForm && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowAssignForm(true)}
              disabled={(budgets ?? []).length === 0}
            >
              <CalendarCheck size={14} className="mr-1.5" />
              Assign budget
            </Button>
          )}
        </div>

        {showAssignForm && (
          <div className="rounded-xl border border-border bg-card p-5">
            <p className="text-sm font-medium mb-4">Assign a budget to a month</p>
            <AssignBudgetForm
              budgets={budgets ?? []}
              onSuccess={() => setShowAssignForm(false)}
              onCancel={() => setShowAssignForm(false)}
            />
          </div>
        )}

        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full rounded-xl" />
            <Skeleton className="h-14 w-full rounded-xl" />
            <Skeleton className="h-14 w-full rounded-xl" />
          </div>
        ) : (
          <AssignmentHistory
            assignments={assignments ?? []}
            budgets={budgets ?? []}
            onDelete={deleteAssignment}
            isDeleting={deletingAssignment}
          />
        )}
      </section>
    </div>
  );
}
