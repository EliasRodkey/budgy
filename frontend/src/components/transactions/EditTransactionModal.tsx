import { Button } from "@/components/ui/button";
import { useCategoryMapping } from "@/hooks/useCategories";
import type { Transaction } from "@/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { TagInput } from "./TagInput";

function ClickToEdit({ value, onCommit, label }: { value: string; onCommit: (v: string) => void; label: string }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  useEffect(() => { setDraft(value); }, [value]);
  if (editing) {
    return (
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => { onCommit(draft); setEditing(false); }}
        onKeyDown={(e) => { if (e.key === "Enter") { onCommit(draft); setEditing(false); } if (e.key === "Escape") { setDraft(value); setEditing(false); } }}
        className="w-full h-8 rounded-md border border-input px-3 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
        aria-label={label}
      />
    );
  }
  return (
    <button
      type="button"
      onClick={() => setEditing(true)}
      className="w-full h-8 text-left px-3 text-sm text-foreground rounded-md border border-transparent hover:border-input hover:bg-muted/40 transition-colors truncate"
      title="Click to edit"
    >
      {draft || <span className="text-muted-foreground italic">—</span>}
    </button>
  );
}

function containsSuspiciousContent(val: string | undefined): boolean {
  if (!val) return false;
  return (
    /<script/i.test(val) ||
    /javascript:/i.test(val) ||
    /on\w+\s*=/i.test(val) ||
    /\b(DROP|INSERT|DELETE|SELECT|UPDATE)\b/i.test(val)
  );
}

const schema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Must be YYYY-MM-DD"),
  description: z.string().optional(),
  accountName: z.string().optional(),
  amount: z.number({ error: "Must be a number" }),
  primaryCategory: z.string().min(1, "Required"),
  detailedCategory: z.string().min(1, "Required"),
  isExcluded: z.boolean(),
  isRepayment: z.boolean(),
  notes: z
    .string()
    .max(300, "Notes must be 300 characters or fewer")
    .optional()
    .refine((val) => !containsSuspiciousContent(val), {
      message: "Notes contain disallowed content",
    }),
  tags: z
    .array(z.string().max(30).regex(/^\S+$/, "Tags cannot contain spaces"))
    .max(10, "Maximum 10 tags allowed")
    .optional(),
});

type FormValues = z.infer<typeof schema>;

interface EditTransactionModalProps {
  transaction: Transaction;
  isPending: boolean;
  availableTags: string[];
  onSave: (id: string, updates: Partial<Transaction>) => void;
  onClose: () => void;
  onDelete?: () => void;
}

interface FieldProps {
  label: string;
  error?: string;
  children: React.ReactNode;
}

function Field({ label, error, children }: FieldProps) {
  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-muted-foreground">{label}</label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

function InputClass(invalid: boolean) {
  return `w-full h-8 rounded-md border px-3 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring ${invalid ? "border-destructive" : "border-input"}`;
}

const MISSING_FIELD_LABELS: Record<string, string> = {
  description: "Description",
  amount: "Amount",
  authorizedDate: "Date",
  primaryCategory: "Category",
  detailedCategory: "Detailed category",
};

function computeMissingFields(tx: Transaction): string[] {
  const checks: Array<[string, boolean]> = [
    ["description", !tx.description],
    ["amount", tx.amount == null],
    ["authorizedDate", !tx.authorizedDate],
    ["primaryCategory", !tx.primaryCategory],
    ["detailedCategory", !tx.detailedCategory],
  ];
  return checks.filter(([, missing]) => missing).map(([key]) => MISSING_FIELD_LABELS[key]);
}

function StatusBadge({ status }: { status: string }) {
  const isUnchecked = status === "Unchecked";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
      isUnchecked
        ? "bg-yellow-400/10 text-yellow-700 dark:text-yellow-400"
        : "bg-green-400/10 text-green-700 dark:text-green-400"
    }`}>
      {status}
    </span>
  );
}

export function EditTransactionModal({ transaction, isPending, availableTags, onSave, onClose, onDelete }: EditTransactionModalProps) {
  const missingFields = computeMissingFields(transaction);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      date: transaction.authorizedDate,
      description: transaction.description,
      accountName: transaction.accountName,
      amount: transaction.amount,
      primaryCategory: transaction.primaryCategory,
      detailedCategory: transaction.detailedCategory,
      isExcluded: transaction.exclude,
      isRepayment: transaction.repayment,
      notes: transaction.notes ?? "",
      tags: transaction.tags ?? [],
    },
  });

  const { data: categoryData } = useCategoryMapping();
  const watchedPrimary = watch("primaryCategory");
  const watchedNotes = watch("notes") ?? "";
  const detailedOptions = (categoryData?.categoryMapping ?? {})[watchedPrimary] ?? [];

  function onSubmit(values: FormValues) {
    onSave(transaction!.id, {
      ...values,
      accountName: values.accountName ?? transaction!.accountName,
      description: values.description ?? transaction!.description,
      notes: values.notes || undefined,
      tags: values.tags?.length ? values.tags : undefined,
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2.5">
            <h2 className="text-sm font-semibold">Edit Transaction</h2>
            {transaction.status && <StatusBadge status={transaction.status} />}
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        {/* Missing fields banner */}
        {missingFields.length > 0 && (
          <div className="mx-5 mt-4 rounded-lg border border-yellow-400/40 bg-yellow-400/5 px-3 py-2.5">
            <p className="text-xs font-medium text-yellow-700 dark:text-yellow-400">
              Missing required fields: {missingFields.join(", ")}
            </p>
            <p className="text-xs text-yellow-600/80 dark:text-yellow-400/70 mt-0.5">
              Fill in the fields above to clear this flag.
            </p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Date" error={errors.date?.message}>
              <input
                type="date"
                {...register("date")}
                className={InputClass(!!errors.date)}
              />
            </Field>
            <Field label="Amount ($)" error={errors.amount?.message}>
              <input
                type="number"
                step="0.01"
                {...register("amount", { valueAsNumber: true })}
                className={InputClass(!!errors.amount)}
              />
            </Field>
          </div>

          <Field label="Description">
            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <ClickToEdit
                  value={field.value ?? ""}
                  onCommit={field.onChange}
                  label="Description"
                />
              )}
            />
          </Field>

          <Field label="Account">
            <Controller
              name="accountName"
              control={control}
              render={({ field }) => (
                <ClickToEdit
                  value={field.value ?? ""}
                  onCommit={field.onChange}
                  label="Account"
                />
              )}
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Category" error={errors.primaryCategory?.message}>
              <Controller
                name="primaryCategory"
                control={control}
                render={({ field }) => (
                  <select
                    value={field.value ?? ""}
                    onBlur={field.onBlur}
                    onChange={(e) => {
                      if (e.target.value !== field.value) {
                        setValue("detailedCategory", "");
                      }
                      field.onChange(e);
                    }}
                    className={InputClass(!!errors.primaryCategory)}
                  >
                    <option value="">Select…</option>
                    {(categoryData?.primaryCategories ?? []).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                )}
              />
            </Field>
            <Field label="Detailed Category" error={errors.detailedCategory?.message}>
              <select
                {...register("detailedCategory")}
                disabled={detailedOptions.length === 0}
                className={InputClass(!!errors.detailedCategory)}
              >
                <option value="">{detailedOptions.length === 0 ? "Select a category first" : "Select…"}</option>
                {detailedOptions.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </Field>
          </div>

          <div className="flex items-center gap-6">
            {(["isExcluded", "isRepayment"] as const).map((field) => (
              <label key={field} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" {...register(field)} className="rounded border-input" />
                {field === "isExcluded" ? "Excluded" : "Repayment"}
              </label>
            ))}
          </div>

          <Field label="Notes" error={errors.notes?.message}>
            <div className="space-y-1">
              <textarea
                {...register("notes")}
                rows={3}
                maxLength={300}
                placeholder="Add a note…"
                className={`w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-none ${errors.notes ? "border-destructive" : "border-input"}`}
              />
              <p className="text-xs text-muted-foreground text-right">{watchedNotes.length}/300</p>
            </div>
          </Field>

          <Field label="Tags" error={errors.tags?.message}>
            <Controller
              name="tags"
              control={control}
              defaultValue={[]}
              render={({ field }) => (
                <TagInput
                  value={field.value ?? []}
                  onChange={field.onChange}
                  availableTags={availableTags}
                  error={errors.tags?.message}
                />
              )}
            />
          </Field>

          <div className="flex justify-between pt-2">
            {onDelete && (
              <Button variant="destructive" type="button" onClick={onDelete}>
                Delete
              </Button>
            )}
            <div className="flex gap-2 ml-auto">
              <Button variant="outline" type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
