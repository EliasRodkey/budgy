import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCategoryMapping } from "@/hooks/useCategories";
import {
  useCreateRule,
  useDeleteRule,
  useRuleMatches,
  useRules,
  useUpdateRule,
} from "@/hooks/useRules";
import { formatDate } from "@/lib/formatters";
import type { Rule } from "@/types";
import type { RuleInput } from "@/api/rules";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ListFilter,
  Pencil,
  PlusCircle,
  RefreshCw,
  Trash2,
  X,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

// ─── Zod schema ───────────────────────────────────────────────────────────────

const ruleSchema = z.object({
  matchDescription: z.string().min(1, "Required"),
  matchAccountName: z.string().min(1, "Required"),
  primaryCategory: z.string().optional(),
  detailedCategory: z.string().optional(),
  exclude: z.boolean().optional(),
});

type RuleFormValues = z.infer<typeof ruleSchema>;

function toRuleInput(values: RuleFormValues): RuleInput {
  return {
    matchDescription: values.matchDescription.trim(),
    matchAccountName: values.matchAccountName.trim(),
    primaryCategory: values.primaryCategory || null,
    detailedCategory: values.detailedCategory || null,
    exclude: values.exclude || null,
  };
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

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function RuleCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <Skeleton className="h-5 w-48" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

// ─── Rule form ────────────────────────────────────────────────────────────────

interface RuleFormProps {
  defaultValues: RuleFormValues;
  isPending: boolean;
  submitLabel: string;
  pendingLabel: string;
  onSubmit: (values: RuleFormValues) => void;
  onCancel: () => void;
}

function RuleForm({
  defaultValues,
  isPending,
  submitLabel,
  pendingLabel,
  onSubmit,
  onCancel,
}: RuleFormProps) {
  const { data: categoryData } = useCategoryMapping();
  const categoryMapping = categoryData?.categoryMapping ?? {};

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RuleFormValues>({
    resolver: zodResolver(ruleSchema),
    defaultValues,
  });

  const primaryCategory = watch("primaryCategory");
  const detailedCategoryOptions = primaryCategory
    ? (categoryMapping[primaryCategory] ?? [])
    : [];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-sm font-medium">Match description</label>
          <input
            type="text"
            placeholder="e.g. TRADER JOES"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...register("matchDescription")}
          />
          {errors.matchDescription && (
            <p className="text-xs text-destructive">{errors.matchDescription.message}</p>
          )}
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium">Match account</label>
          <input
            type="text"
            placeholder="e.g. Chase Sapphire"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...register("matchAccountName")}
          />
          {errors.matchAccountName && (
            <p className="text-xs text-destructive">{errors.matchAccountName.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-sm font-medium">Set primary category</label>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...register("primaryCategory")}
          >
            <option value="">No change</option>
            {(categoryData?.primaryCategories ?? []).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium">Set detailed category</label>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            disabled={!primaryCategory}
            {...register("detailedCategory")}
          >
            <option value="">No change</option>
            {detailedCategoryOptions.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" className="rounded border-input" {...register("exclude")} />
        <span className="text-sm">Exclude matching transactions from budgets/analytics</span>
      </label>

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

// ─── Create rule form ─────────────────────────────────────────────────────────

function CreateRuleForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) {
  const { mutate, isPending, error } = useCreateRule();

  const defaultValues: RuleFormValues = {
    matchDescription: "",
    matchAccountName: "",
    primaryCategory: "",
    detailedCategory: "",
    exclude: false,
  };

  function onSubmit(values: RuleFormValues) {
    mutate(toRuleInput(values), { onSuccess });
  }

  return (
    <div className="space-y-2">
      <RuleForm
        defaultValues={defaultValues}
        isPending={isPending}
        submitLabel="Create rule"
        pendingLabel="Saving…"
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
      {error && <p className="text-xs text-destructive">{error.message}</p>}
    </div>
  );
}

// ─── Edit rule form ───────────────────────────────────────────────────────────

function EditRuleForm({ rule, onSuccess, onCancel }: { rule: Rule; onSuccess: () => void; onCancel: () => void }) {
  const { mutate, isPending, error } = useUpdateRule();

  const defaultValues: RuleFormValues = {
    matchDescription: rule.matchDescription,
    matchAccountName: rule.matchAccountName,
    primaryCategory: rule.primaryCategory ?? "",
    detailedCategory: rule.detailedCategory ?? "",
    exclude: rule.exclude ?? false,
  };

  function onSubmit(values: RuleFormValues) {
    mutate({ id: rule.id, payload: toRuleInput(values) }, { onSuccess });
  }

  return (
    <div className="space-y-2">
      <RuleForm
        defaultValues={defaultValues}
        isPending={isPending}
        submitLabel="Save changes"
        pendingLabel="Saving…"
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
      {error && <p className="text-xs text-destructive">{error.message}</p>}
    </div>
  );
}

// ─── Delete rule dialog ───────────────────────────────────────────────────────

function DeleteRuleDialog({
  rule,
  isPending,
  onConfirm,
  onClose,
}: {
  rule: Rule;
  isPending: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-destructive" />
            <h2 className="text-sm font-semibold">Delete rule</h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <p className="text-sm text-muted-foreground">
            Delete the rule matching{" "}
            <span className="font-medium text-foreground">"{rule.matchDescription}"</span> on{" "}
            <span className="font-medium text-foreground">{rule.matchAccountName}</span>?
            This stops future application of the rule but does not revert changes already made.
          </p>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose} disabled={isPending}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={isPending} onClick={onConfirm}>
              {isPending ? "Deleting…" : "Delete"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Matched transactions preview ────────────────────────────────────────────

function MatchesPreview({ ruleId }: { ruleId: number }) {
  const { data, isLoading, isError } = useRuleMatches(ruleId);

  if (isLoading) {
    return (
      <div className="space-y-2 pt-3 border-t border-border">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <p className="text-xs text-destructive pt-3 border-t border-border">
        Failed to load matched transactions.
      </p>
    );
  }

  if (data.matchCount === 0) {
    return (
      <p className="text-xs text-muted-foreground pt-3 border-t border-border">
        No transactions currently match this rule.
      </p>
    );
  }

  return (
    <div className="space-y-2 pt-3 border-t border-border">
      <p className="text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{data.matchCount}</span> matching transaction
        {data.matchCount !== 1 ? "s" : ""}
        {data.transactions.length < data.matchCount && (
          <> (showing first {data.transactions.length})</>
        )}
      </p>
      <ul className="rounded-lg border border-border overflow-hidden divide-y divide-border max-h-48 overflow-y-auto">
        {data.transactions.map((tx) => (
          <li key={tx.id} className="flex items-center justify-between gap-3 px-3 py-1.5 text-xs">
            <span className="truncate">{tx.description}</span>
            <span className="text-muted-foreground shrink-0">{formatDate(tx.authorizedDate)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── Rule card ────────────────────────────────────────────────────────────────

function RuleCard({ rule, onDeleteRequest }: { rule: Rule; onDeleteRequest: (rule: Rule) => void }) {
  const [editing, setEditing] = useState(false);
  const [showMatches, setShowMatches] = useState(false);

  const categoryAction = [rule.primaryCategory, rule.detailedCategory].filter(Boolean).join(" › ");

  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <p className="text-sm font-medium truncate">
            "{rule.matchDescription}" on {rule.matchAccountName}
          </p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {categoryAction && (
              <span>
                Set category: <span className="text-foreground font-medium">{categoryAction}</span>
              </span>
            )}
            {rule.exclude && (
              <span className="text-foreground font-medium">Exclude from budgets/analytics</span>
            )}
            {!categoryAction && !rule.exclude && (
              <span>No actions configured</span>
            )}
          </div>
        </div>

        {!editing && (
          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground"
              onClick={() => setShowMatches((v) => !v)}
              title="Show matched transactions"
            >
              <ListFilter size={14} />
              {showMatches ? <ChevronUp size={14} className="ml-1" /> : <ChevronDown size={14} className="ml-1" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground"
              onClick={() => setEditing(true)}
              title="Edit rule"
            >
              <Pencil size={14} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-destructive hover:text-destructive"
              onClick={() => onDeleteRequest(rule)}
              title="Delete rule"
            >
              <Trash2 size={14} />
            </Button>
          </div>
        )}
      </div>

      {editing && (
        <div className="border-t border-border pt-4">
          <EditRuleForm rule={rule} onSuccess={() => setEditing(false)} onCancel={() => setEditing(false)} />
        </div>
      )}

      {showMatches && !editing && <MatchesPreview ruleId={rule.id} />}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Rules() {
  const { data: rules, isLoading, isError, refetch } = useRules();
  const { mutate: deleteRule, isPending: deletingRule } = useDeleteRule();

  const [showCreate, setShowCreate] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Rule | null>(null);

  function handleDeleteConfirm() {
    if (!deleteTarget) return;
    deleteRule(deleteTarget.id, { onSuccess: () => setDeleteTarget(null) });
  }

  return (
    <div className="p-6 space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold">Rules</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Automatically categorize, exclude, or tag transactions that match a description and account.
        </p>
      </div>

      {isError && (
        <ErrorCard message="Failed to load rules." onRetry={() => refetch()} />
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Your rules</h2>
          {!showCreate && (
            <Button size="sm" onClick={() => setShowCreate(true)}>
              <PlusCircle size={14} className="mr-1.5" />
              New rule
            </Button>
          )}
        </div>

        {showCreate && (
          <div className="rounded-xl border border-border bg-card p-5">
            <p className="text-sm font-medium mb-4">Create new rule</p>
            <CreateRuleForm
              onSuccess={() => setShowCreate(false)}
              onCancel={() => setShowCreate(false)}
            />
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            <RuleCardSkeleton />
            <RuleCardSkeleton />
          </div>
        ) : (rules ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground py-2">
            No rules yet. Create one above, or save one from the transaction edit dialog.
          </p>
        ) : (
          <div className="space-y-3">
            {(rules ?? []).map((rule) => (
              <RuleCard key={rule.id} rule={rule} onDeleteRequest={setDeleteTarget} />
            ))}
          </div>
        )}
      </section>

      {deleteTarget && (
        <DeleteRuleDialog
          rule={deleteTarget}
          isPending={deletingRule}
          onConfirm={handleDeleteConfirm}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
