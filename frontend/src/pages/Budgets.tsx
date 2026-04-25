import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCategoryMapping } from "@/hooks/useCategories";
import {
  useBudgetAssignments,
  useBudgets,
  useCreateBudget,
  useCreateBudgetAssignment,
  useDeleteBudget,
  useUpdateBudget,
} from "@/hooks/useBudgets";
import { getBudgetPeriod, getEffectiveBudget } from "@/lib/budget";
import { currentMonth, formatCurrency, formatDate, formatMonth } from "@/lib/formatters";
import type { Budget, BudgetAssignment } from "@/types";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  AlertTriangle,
  CalendarCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Pencil,
  PlusCircle,
  RefreshCw,
  Trash2,
  Wallet,
  X,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { z } from "zod";

// ─── Non-budget primary categories (excluded from spending limit form) ────────

const NON_BUDGET_CATEGORIES = new Set([
  "Income", "Transfers", "Debt payments", "Investments", "Bank fees",
]);

// ─── Chart colors ─────────────────────────────────────────────────────────────

const CHART_COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#14b8a6",
];

// ─── Zod schemas ──────────────────────────────────────────────────────────────

const budgetSchema = z.object({
  categoryLimits: z.record(
    z.string(),
    z.number({ error: "Must be a number" }).min(0, "Must be ≥ 0"),
  ),
  incomeEstimate: z.number({ error: "Must be a number" }).min(0, "Must be ≥ 0"),
  note: z.string().max(200, "Max 200 characters").optional(),
});

type BudgetFormValues = z.infer<typeof budgetSchema>;

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

// ─── Info tooltip ─────────────────────────────────────────────────────────────

function InfoTooltip({ text }: { text: string }) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="More info"
          >
            <HelpCircle size={14} />
          </button>
        </TooltipTrigger>
        <TooltipContent side="right" className="max-w-64 text-xs leading-relaxed">
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
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
          No budget is currently active. Use "Assign as current" on a budget below.
        </p>
      </div>
    );
  }

  const period = getBudgetPeriod(budget.id, assignments);
  const limitTotal = Object.values(budget.categoryLimits).reduce((s, v) => s + v, 0);

  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 space-y-2">
      <div className="flex items-center gap-2 text-primary">
        <CheckCircle2 size={16} className="shrink-0" />
        <span className="text-xs font-medium uppercase tracking-wide">Active budget</span>
      </div>
      <div className="flex items-baseline gap-3 flex-wrap">
        {period ? (
          <span className="text-lg font-semibold">
            {formatMonth(period.from)} – {period.to ? formatMonth(period.to) : "present"}
          </span>
        ) : (
          <span className="text-lg font-semibold">Created {formatDate(budget.dateCreated)}</span>
        )}
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
      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 border-t border-primary/20 pt-3 mt-1 text-sm">
        {Object.entries(budget.categoryLimits).map(([category, limit]) => (
          <div key={category} className="flex justify-between gap-2">
            <span className="text-muted-foreground truncate">{category}</span>
            <span className="font-medium tabular-nums">{formatCurrency(limit)}</span>
          </div>
        ))}
      </div>
      {budget.note && (
        <p className="text-xs text-muted-foreground border-t border-primary/20 pt-2 mt-1">
          {budget.note}
        </p>
      )}
    </div>
  );
}

// ─── Budget delete dialog ─────────────────────────────────────────────────────

interface BudgetDeleteDialogProps {
  budget: Budget;
  allBudgets: Budget[];
  assignments: BudgetAssignment[];
  isPending: boolean;
  onConfirm: (replacementBudgetId: string | null) => void;
  onClose: () => void;
}

function BudgetDeleteDialog({
  budget,
  allBudgets,
  assignments,
  isPending,
  onConfirm,
  onClose,
}: BudgetDeleteDialogProps) {
  const [replacementId, setReplacementId] = useState("");

  // Find all months where this budget is the effective budget
  const affectedMonths: string[] = [];
  if (assignments.length > 0) {
    const earliest = assignments
      .filter((a) => a.budgetId === budget.id)
      .sort((a, b) => a.effectiveFrom.localeCompare(b.effectiveFrom))[0];

    if (earliest) {
      const start = earliest.effectiveFrom;
      const end = currentMonth();
      let cursor = start;
      while (cursor <= end) {
        const effective = getEffectiveBudget(assignments, cursor);
        if (effective?.budgetId === budget.id) {
          affectedMonths.push(cursor);
        }
        // advance cursor by 1 month
        const [y, m] = cursor.split("-").map(Number);
        cursor = m === 12
          ? `${y + 1}-01`
          : `${y}-${String(m + 1).padStart(2, "0")}`;
      }
    }
  }

  const otherBudgets = allBudgets.filter((b) => b.id !== budget.id);
  const hasAffectedMonths = affectedMonths.length > 0;
  const canConfirm = !hasAffectedMonths || replacementId !== "";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-destructive" />
            <h2 className="text-sm font-semibold">Delete Budget</h2>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {hasAffectedMonths ? (
            <>
              <p className="text-sm text-muted-foreground">
                This budget is currently assigned to{" "}
                <span className="font-medium text-foreground">
                  {affectedMonths.length} month{affectedMonths.length !== 1 ? "s" : ""}
                </span>
                . You must choose a replacement before deleting.
              </p>

              <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-1 max-h-32 overflow-y-auto">
                {affectedMonths.map((m) => (
                  <p key={m} className="text-xs text-muted-foreground">{formatMonth(m)}</p>
                ))}
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Replacement budget</label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  value={replacementId}
                  onChange={(e) => setReplacementId(e.target.value)}
                >
                  <option value="">Select a replacement…</option>
                  {otherBudgets.map((b) => {
                    const period = getBudgetPeriod(b.id, assignments);
                    const label = period
                      ? `${formatMonth(period.from)}${period.to ? ` – ${formatMonth(period.to)}` : " – present"}`
                      : `Created ${formatDate(b.dateCreated)}`;
                    return (
                      <option key={b.id} value={b.id}>
                        {label} — Net {formatCurrency(b.netGainOrLoss)}
                      </option>
                    );
                  })}
                </select>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Are you sure you want to delete this budget? This action cannot be undone.
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose} disabled={isPending}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={isPending || !canConfirm}
              onClick={() => onConfirm(replacementId || null)}
            >
              {isPending ? "Deleting…" : "Delete"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Shared budget form fields ────────────────────────────────────────────────

interface BudgetFormProps {
  defaultValues: BudgetFormValues;
  spendingCategories: string[];
  isPending: boolean;
  submitLabel: string;
  pendingLabel: string;
  onSubmit: (values: BudgetFormValues) => void;
  onCancel: () => void;
}

function BudgetForm({
  defaultValues,
  spendingCategories,
  isPending,
  submitLabel,
  pendingLabel,
  onSubmit,
  onCancel,
}: BudgetFormProps) {
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
  const totalLimits = spendingCategories.reduce(
    (sum, c) => sum + (Number(watched.categoryLimits?.[c]) || 0),
    0,
  );
  const net = (Number(watched.incomeEstimate) || 0) - totalLimits;

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
          {spendingCategories.map((category) => (
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

      <div className="space-y-1">
        <label className="text-sm font-medium">Note (optional)</label>
        <input
          type="text"
          placeholder="e.g. Post-raise revision"
          maxLength={200}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("note")}
        />
        {errors.note && (
          <p className="text-xs text-destructive">{errors.note.message}</p>
        )}
      </div>

      {/* Live net calculation */}
      <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          <span className="text-foreground font-medium">
            {formatCurrency(Number(watched.incomeEstimate) || 0)}
          </span>
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
          {isPending ? pendingLabel : submitLabel}
        </Button>
      </div>
    </form>
  );
}

// ─── Create budget form ───────────────────────────────────────────────────────

interface CreateBudgetFormProps {
  onSuccess: () => void;
  onCancel: () => void;
  prefillBudget?: Budget;
}

function CreateBudgetForm({ onSuccess, onCancel, prefillBudget }: CreateBudgetFormProps) {
  const { mutate, isPending } = useCreateBudget();
  const { data: categoryData } = useCategoryMapping();
  const spendingCategories = (categoryData?.primaryCategories ?? []).filter(
    (c) => !NON_BUDGET_CATEGORIES.has(c),
  );

  const defaultValues: BudgetFormValues = prefillBudget
    ? {
        categoryLimits: Object.fromEntries(
          spendingCategories.map((c) => [c, prefillBudget.categoryLimits[c] ?? 0]),
        ),
        incomeEstimate: prefillBudget.monthlyIncomeEstimate,
        note: prefillBudget.note ?? "",
      }
    : {
        categoryLimits: Object.fromEntries(spendingCategories.map((c) => [c, 0])),
        incomeEstimate: 0,
        note: "",
      };

  function onSubmit(values: BudgetFormValues) {
    const income = Number(values.incomeEstimate) || 0;
    const limits: Record<string, number> = {};
    for (const [cat, val] of Object.entries(values.categoryLimits)) {
      const n = Number(val);
      if (n > 0) limits[cat] = n;
    }
    const limitSum = Object.values(limits).reduce((s, v) => s + v, 0);
    mutate(
      {
        categoryLimits: limits,
        monthlyIncomeEstimate: income,
        netGainOrLoss: income - limitSum,
        note: values.note?.trim() || null,
      },
      { onSuccess },
    );
  }

  return (
    <BudgetForm
      defaultValues={defaultValues}
      spendingCategories={spendingCategories}
      isPending={isPending}
      submitLabel="Create budget"
      pendingLabel="Saving…"
      onSubmit={onSubmit}
      onCancel={onCancel}
    />
  );
}

// ─── Edit budget form ─────────────────────────────────────────────────────────

interface EditBudgetFormProps {
  budget: Budget;
  onSuccess: () => void;
  onCancel: () => void;
}

function EditBudgetForm({ budget, onSuccess, onCancel }: EditBudgetFormProps) {
  const { mutate, isPending } = useUpdateBudget();
  const { data: categoryData } = useCategoryMapping();
  const spendingCategories = (categoryData?.primaryCategories ?? []).filter(
    (c) => !NON_BUDGET_CATEGORIES.has(c),
  );

  const limitSum = Object.values(budget.categoryLimits).reduce((s, v) => s + v, 0);
  const defaultValues: BudgetFormValues = {
    categoryLimits: Object.fromEntries(
      spendingCategories.map((c) => [c, budget.categoryLimits[c] ?? 0]),
    ),
    incomeEstimate: budget.monthlyIncomeEstimate,
    note: budget.note ?? "",
  };

  function onSubmit(values: BudgetFormValues) {
    const income = Number(values.incomeEstimate) || 0;
    const limits: Record<string, number> = {};
    for (const [cat, val] of Object.entries(values.categoryLimits)) {
      const n = Number(val);
      if (n > 0) limits[cat] = n;
    }
    const newLimitSum = Object.values(limits).reduce((s, v) => s + v, 0);
    mutate(
      {
        id: budget.id,
        payload: {
          categoryLimits: limits,
          monthlyIncomeEstimate: income,
          netGainOrLoss: income - newLimitSum,
          note: values.note?.trim() || null,
        },
      },
      { onSuccess },
    );
  }

  return (
    <BudgetForm
      defaultValues={defaultValues}
      spendingCategories={spendingCategories}
      isPending={isPending}
      submitLabel="Save changes"
      pendingLabel="Saving…"
      onSubmit={onSubmit}
      onCancel={onCancel}
    />
  );
}

// ─── Edit warning dialog ──────────────────────────────────────────────────────

interface EditWarningDialogProps {
  pastMonths: string[];
  onCreateNew: () => void;
  onClose: () => void;
}

function EditWarningDialog({ pastMonths, onCreateNew, onClose }: EditWarningDialogProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-500" />
            <h2 className="text-sm font-semibold">Unable to edit budget</h2>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <p className="text-sm text-muted-foreground">
            This budget is assigned to past months that can no longer be changed. Editing
            it in place would retroactively alter those months.
          </p>

          <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-1 max-h-32 overflow-y-auto">
            {pastMonths.map((m) => (
              <p key={m} className="text-xs text-muted-foreground">{formatMonth(m)}</p>
            ))}
          </div>

          <p className="text-sm text-muted-foreground">
            Would you like to create a new budget pre-filled with these values instead?
          </p>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={onCreateNew}>
              Create new budget
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Budget card ──────────────────────────────────────────────────────────────

interface BudgetCardProps {
  budget: Budget;
  isActive: boolean;
  assignments: BudgetAssignment[];
  allBudgets: Budget[];
  onDeleteRequest: (budget: Budget) => void;
  onAssignAsCurrent: (budgetId: string) => void;
  onCreateFromBudget: (budget: Budget) => void;
  isAssigning: boolean;
}

function BudgetCard({
  budget,
  isActive,
  assignments,
  allBudgets,
  onDeleteRequest,
  onAssignAsCurrent,
  onCreateFromBudget,
  isAssigning,
}: BudgetCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showEditWarning, setShowEditWarning] = useState(false);

  const limits = Object.entries(budget.categoryLimits);
  const period = getBudgetPeriod(budget.id, assignments);

  // Months before the current month where this budget was the effective budget
  const pastMonthsAssigned = (() => {
    const own = assignments.filter((a) => a.budgetId === budget.id);
    if (own.length === 0) return [];
    const earliest = own.sort((a, b) => a.effectiveFrom.localeCompare(b.effectiveFrom))[0];
    const past: string[] = [];
    const today = currentMonth();
    let cursor = earliest.effectiveFrom;
    while (cursor < today) {
      if (getEffectiveBudget(assignments, cursor)?.budgetId === budget.id) {
        past.push(cursor);
      }
      const [y, m] = cursor.split("-").map(Number);
      cursor = m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, "0")}`;
    }
    return past;
  })();

  function handleEditClick() {
    if (pastMonthsAssigned.length > 0) {
      setShowEditWarning(true);
    } else {
      setEditing(true);
      setExpanded(false);
    }
  }

  return (
    <div
      className={`rounded-xl border bg-card p-5 space-y-3 ${
        isActive ? "border-primary/40" : "border-border"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <Wallet size={15} className="text-muted-foreground" />
            <span className="text-sm font-medium">
              {period
                ? `${formatMonth(period.from)} – ${period.to ? formatMonth(period.to) : "present"}`
                : `Created ${formatDate(budget.dateCreated)}`}
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
          {isActive && !editing && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground"
              onClick={handleEditClick}
              title="Edit this budget"
            >
              <Pencil size={14} />
            </Button>
          )}
          {!isActive && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-muted-foreground hover:text-primary"
                    onClick={() => onAssignAsCurrent(budget.id)}
                    disabled={isAssigning}
                  >
                    <CalendarCheck size={14} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  Assign as current month's budget
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-muted-foreground"
            onClick={() => { setExpanded((e) => !e); setEditing(false); }}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-destructive hover:text-destructive"
            onClick={() => onDeleteRequest(budget)}
          >
            <Trash2 size={14} />
          </Button>
        </div>
      </div>

      {editing && (
        <div className="border-t border-border pt-4">
          <EditBudgetForm
            budget={budget}
            onSuccess={() => setEditing(false)}
            onCancel={() => setEditing(false)}
          />
        </div>
      )}

      {expanded && !editing && (
        <div className="space-y-3 border-t border-border pt-3">
          <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
            {limits.map(([category, limit]) => (
              <div key={category} className="flex justify-between gap-2">
                <span className="text-muted-foreground truncate">{category}</span>
                <span className="font-medium tabular-nums">{formatCurrency(limit)}</span>
              </div>
            ))}
          </div>
          {budget.note && (
            <p className="text-xs text-muted-foreground border-t border-border/50 pt-2">
              {budget.note}
            </p>
          )}
        </div>
      )}

      {showEditWarning && (
        <EditWarningDialog
          pastMonths={pastMonthsAssigned}
          onCreateNew={() => {
            setShowEditWarning(false);
            onCreateFromBudget(budget);
          }}
          onClose={() => setShowEditWarning(false)}
        />
      )}
    </div>
  );
}

// ─── Budget limits chart ──────────────────────────────────────────────────────

type ChartView = "total" | "per-category";

/** Compact axis label: "Jan '25" */
function shortMonth(yyyyMm: string): string {
  const [y, m] = yyyyMm.split("-").map(Number);
  const date = new Date(y, m - 1, 1);
  const mon = date.toLocaleDateString("en-US", { month: "short" });
  return `${mon} '${String(y).slice(2)}`;
}

interface BudgetLimitsChartProps {
  budgets: Budget[];
  assignments: BudgetAssignment[];
}

function BudgetLimitsChart({ budgets, assignments }: BudgetLimitsChartProps) {
  const [view, setView] = useState<ChartView>("total");

  if (assignments.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-2">
        No assignments yet. Assign a budget above to see how limits change over time.
      </p>
    );
  }

  // Build month range from earliest assignment to current month
  const sortedAssignments = [...assignments].sort((a, b) =>
    a.effectiveFrom.localeCompare(b.effectiveFrom),
  );
  const startMonth = sortedAssignments[0].effectiveFrom;
  const endMonth = currentMonth();

  const months: string[] = [];
  let cursor = startMonth;
  while (cursor <= endMonth) {
    months.push(cursor);
    const [y, m] = cursor.split("-").map(Number);
    cursor = m === 12
      ? `${y + 1}-01`
      : `${y}-${String(m + 1).padStart(2, "0")}`;
  }

  // All unique categories across all budgets
  const allCategories = Array.from(
    new Set(budgets.flatMap((b) => Object.keys(b.categoryLimits))),
  ).sort();

  // Build chart data
  const data = months.map((month) => {
    const assignment = getEffectiveBudget(assignments, month);
    const budget = assignment ? budgets.find((b) => b.id === assignment.budgetId) : null;
    const row: Record<string, string | number> = {
      month: shortMonth(month),
      monthFull: month,
    };
    if (view === "total") {
      row.Total = budget
        ? Object.values(budget.categoryLimits).reduce((s, v) => s + v, 0)
        : 0;
    } else {
      for (const cat of allCategories) {
        row[cat] = budget?.categoryLimits[cat] ?? 0;
      }
    }
    return row;
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button
          variant={view === "total" ? "default" : "outline"}
          size="sm"
          onClick={() => setView("total")}
        >
          Total
        </Button>
        <Button
          variant={view === "per-category" ? "default" : "outline"}
          size="sm"
          onClick={() => setView("per-category")}
        >
          Per category
        </Button>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              tickLine={false}
              axisLine={false}
              width={48}
            />
            <RechartsTooltip
              formatter={(value: number, name: string) => [formatCurrency(value), name]}
              labelFormatter={(label, payload) => {
                const monthFull = payload?.[0]?.payload?.monthFull;
                return monthFull ? formatMonth(monthFull) : label;
              }}
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
            {view === "total" ? (
              <Line
                type="stepAfter"
                dataKey="Total"
                stroke={CHART_COLORS[0]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ) : (
              <>
                {allCategories.map((cat, i) => (
                  <Line
                    key={cat}
                    type="stepAfter"
                    dataKey={cat}
                    stroke={CHART_COLORS[i % CHART_COLORS.length]}
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 3 }}
                  />
                ))}
                <Legend wrapperStyle={{ fontSize: "11px" }} />
              </>
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
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
  const { mutate: assignAsCurrent, isPending: assigning } = useCreateBudgetAssignment();

  const [showCreateBudget, setShowCreateBudget] = useState(false);
  const [prefillBudget, setPrefillBudget] = useState<Budget | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Budget | null>(null);

  function handleCreateFromBudget(budget: Budget) {
    setPrefillBudget(budget);
    setShowCreateBudget(true);
  }

  const isLoading = loadingBudgets || loadingAssignments;
  const isError = errorBudgets || errorAssignments;

  const activeAssignment =
    budgets && assignments ? getEffectiveBudget(assignments, currentMonth()) : null;

  function handleAssignAsCurrent(budgetId: string) {
    assignAsCurrent({ budgetId, effectiveFrom: currentMonth(), note: null });
  }

  function handleDeleteConfirm(replacementBudgetId: string | null) {
    if (!deleteTarget) return;

    const affectedAssignmentIds = (assignments ?? [])
      .filter((a) => a.budgetId === deleteTarget.id)
      .map((a) => a.id);

    if (replacementBudgetId && affectedAssignmentIds.length > 0) {
      // Reassign all affected months to the replacement, then delete
      // Compute affected months (same logic as BudgetDeleteDialog)
      const sortedOwn = (assignments ?? [])
        .filter((a) => a.budgetId === deleteTarget.id)
        .sort((a, b) => a.effectiveFrom.localeCompare(b.effectiveFrom));

      if (sortedOwn.length > 0) {
        const start = sortedOwn[0].effectiveFrom;
        const end = currentMonth();
        let cursor = start;
        while (cursor <= end) {
          const effective = getEffectiveBudget(assignments ?? [], cursor);
          if (effective?.budgetId === deleteTarget.id) {
            assignAsCurrent({ budgetId: replacementBudgetId, effectiveFrom: cursor, note: null });
          }
          const [y, m] = cursor.split("-").map(Number);
          cursor = m === 12
            ? `${y + 1}-01`
            : `${y}-${String(m + 1).padStart(2, "0")}`;
        }
      }
    }

    deleteBudget(deleteTarget.id, {
      onSuccess: () => setDeleteTarget(null),
    });
  }

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

      {/* ── Budget limits over time ── */}
      <section className="space-y-3">
        <div className="flex items-center gap-1.5">
          <h2 className="text-base font-semibold">Limits over time</h2>
          <InfoTooltip text="Shows how your budget limits have changed as you've switched between budgets. Lines step at each transition point." />
        </div>
        {isLoading ? (
          <Skeleton className="h-64 w-full rounded-xl" />
        ) : (
          <BudgetLimitsChart
            budgets={budgets ?? []}
            assignments={assignments ?? []}
          />
        )}
      </section>

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
          <div className="flex items-center gap-1.5">
            <h2 className="text-base font-semibold">Budgets</h2>
            <InfoTooltip text="Only the active budget can be edited. Past budgets are read-only — use 'Assign as current' to reactivate one. Assignments lock at month-end." />
          </div>
          {!showCreateBudget && (
            <Button size="sm" onClick={() => setShowCreateBudget(true)}>
              <PlusCircle size={14} className="mr-1.5" />
              New budget
            </Button>
          )}
        </div>

        {showCreateBudget && (
          <div className="rounded-xl border border-border bg-card p-5">
            <p className="text-sm font-medium mb-4">
              {prefillBudget ? "Create new budget (pre-filled from existing)" : "Create new budget"}
            </p>
            <CreateBudgetForm
              prefillBudget={prefillBudget ?? undefined}
              onSuccess={() => { setShowCreateBudget(false); setPrefillBudget(null); }}
              onCancel={() => { setShowCreateBudget(false); setPrefillBudget(null); }}
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
                assignments={assignments ?? []}
                allBudgets={budgets ?? []}
                onDeleteRequest={setDeleteTarget}
                onAssignAsCurrent={handleAssignAsCurrent}
                onCreateFromBudget={handleCreateFromBudget}
                isAssigning={assigning}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── Delete dialog ── */}
      {deleteTarget && (
        <BudgetDeleteDialog
          budget={deleteTarget}
          allBudgets={budgets ?? []}
          assignments={assignments ?? []}
          isPending={deletingBudget}
          onConfirm={handleDeleteConfirm}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
