import { Button } from "@/components/ui/button";
import { CATEGORY_MAPPING } from "@/constants/categories";
import type { Transaction } from "@/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { TagInput } from "./TagInput";

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
  description: z.string().min(1, "Required"),
  merchant: z.string().min(1, "Required"),
  amount: z.number({ error: "Must be a number" }),
  primaryCategory: z.string().min(1, "Required"),
  detailedCategory: z.string().min(1, "Required"),
  isFlagged: z.boolean(),
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
  transaction: Transaction | null;
  isPending: boolean;
  availableTags: string[];
  onSave: (id: string, updates: Partial<Transaction>) => void;
  onClose: () => void;
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

export function EditTransactionModal({ transaction, isPending, availableTags, onSave, onClose }: EditTransactionModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const watchedPrimary = watch("primaryCategory");
  const watchedNotes = watch("notes") ?? "";
  const detailedOptions = CATEGORY_MAPPING[watchedPrimary] ?? [];

  // Reset detailed category when primary category changes
  const [prevPrimary, setPrevPrimary] = useState<string | undefined>(undefined);
  useEffect(() => {
    if (prevPrimary !== undefined && watchedPrimary !== prevPrimary) {
      setValue("detailedCategory", "");
    }
    setPrevPrimary(watchedPrimary);
  }, [watchedPrimary, prevPrimary, setValue]);

  useEffect(() => {
    if (transaction) {
      reset({
        date: transaction.authorizedDate,
        description: transaction.description,
        merchant: transaction.account_name,
        amount: transaction.amount,
        primaryCategory: transaction.primaryCategory,
        detailedCategory: transaction.detailedCategory,
        isFlagged: transaction.isFlagged,
        isExcluded: transaction.exclude,
        isRepayment: transaction.repayment,
        notes: transaction.notes ?? "",
        tags: transaction.tags ?? [],
      });
      setPrevPrimary(transaction.primaryCategory);
    }
  }, [transaction, reset]);

  if (!transaction) return null;

  function onSubmit(values: FormValues) {
    onSave(transaction!.id, {
      ...values,
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
          <h2 className="text-sm font-semibold">Edit Transaction</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

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

          <Field label="Description" error={errors.description?.message}>
            <input
              type="text"
              {...register("description")}
              className={InputClass(!!errors.description)}
            />
          </Field>

          <Field label="Merchant" error={errors.merchant?.message}>
            <input
              type="text"
              {...register("merchant")}
              className={InputClass(!!errors.merchant)}
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Category" error={errors.primaryCategory?.message}>
              <select
                {...register("primaryCategory")}
                className={InputClass(!!errors.primaryCategory)}
              >
                <option value="">Select…</option>
                {Object.keys(CATEGORY_MAPPING).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
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
            {(["isFlagged", "isExcluded", "isRepayment"] as const).map((field) => (
              <label key={field} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" {...register(field)} className="rounded border-input" />
                {field === "isFlagged" ? "Flagged" : field === "isExcluded" ? "Excluded" : "Repayment"}
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

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
