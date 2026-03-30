import { Button } from "@/components/ui/button";
import type { Transaction } from "@/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { X } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

const PRIMARY_CATEGORIES = [
  "Income",
  "Transfers",
  "Debt payments",
  "Investments",
  "Bank fees",
  "Food & drink",
  "Shopping",
  "Housing & utilities",
  "Health & wellness",
  "Entertainment",
  "Insurance",
  "Services",
  "Transportation",
  "Travel",
  "Government & charity",
  "Other",
];

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
});

type FormValues = z.infer<typeof schema>;

interface EditTransactionModalProps {
  transaction: Transaction | null;
  isPending: boolean;
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

export function EditTransactionModal({ transaction, isPending, onSave, onClose }: EditTransactionModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (transaction) {
      reset({
        date: transaction.date,
        description: transaction.description,
        merchant: transaction.merchant,
        amount: transaction.amount,
        primaryCategory: transaction.primaryCategory,
        detailedCategory: transaction.detailedCategory,
        isFlagged: transaction.isFlagged,
        isExcluded: transaction.isExcluded,
        isRepayment: transaction.isRepayment,
      });
    }
  }, [transaction, reset]);

  if (!transaction) return null;

  function onSubmit(values: FormValues) {
    onSave(transaction!.id, values);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-lg">
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
            <Field label="Primary Category" error={errors.primaryCategory?.message}>
              <select
                {...register("primaryCategory")}
                className={InputClass(!!errors.primaryCategory)}
              >
                <option value="">Select…</option>
                {PRIMARY_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </Field>
            <Field label="Detailed Category" error={errors.detailedCategory?.message}>
              <input
                type="text"
                {...register("detailedCategory")}
                className={InputClass(!!errors.detailedCategory)}
              />
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
