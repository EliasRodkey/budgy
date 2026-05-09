import { Button } from "@/components/ui/button";
import { useCategoryMapping } from "@/hooks/useCategories";
import { useCreateTransaction } from "@/hooks/useTransactions";
import { DuplicateTransactionError, type NewTransactionFields } from "@/api/transactions";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle, X } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

const schema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Must be YYYY-MM-DD"),
  description: z.string().min(1, "Required"),
  amount: z.number({ error: "Must be a number" }),
  accountName: z.string().min(1, "Required"),
  primaryCategory: z.string().min(1, "Required"),
  detailedCategory: z.string().min(1, "Required"),
});

type FormValues = z.infer<typeof schema>;

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

interface AddTransactionModalProps {
  onClose: () => void;
}

export function AddTransactionModal({ onClose }: AddTransactionModalProps) {
  const [duplicateCount, setDuplicateCount] = useState<number | null>(null);
  const [pendingFields, setPendingFields] = useState<NewTransactionFields | null>(null);

  const { mutate: createTx, isPending } = useCreateTransaction();
  const { data: categoryData } = useCategoryMapping();

  const today = new Date().toISOString().slice(0, 10);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { date: today },
  });

  const watchedPrimary = watch("primaryCategory");
  const detailedOptions = (categoryData?.categoryMapping ?? {})[watchedPrimary] ?? [];

  function submit(values: FormValues, force = false) {
    const fields: NewTransactionFields = {
      date: values.date,
      description: values.description,
      amount: values.amount,
      accountName: values.accountName,
      primaryCategory: values.primaryCategory,
      detailedCategory: values.detailedCategory,
    };

    createTx({ fields, force }, {
      onSuccess: () => onClose(),
      onError: (err) => {
        if (err instanceof DuplicateTransactionError) {
          setDuplicateCount(err.count);
          setPendingFields(fields);
        }
      },
    });
  }

  function onSubmit(values: FormValues) {
    submit(values, false);
  }

  function forceAdd() {
    if (!pendingFields) return;
    createTx({ fields: pendingFields, force: true }, {
      onSuccess: () => onClose(),
    });
  }

  function dismissDuplicate() {
    setDuplicateCount(null);
    setPendingFields(null);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-sm font-semibold">Add Transaction</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        {duplicateCount !== null && (
          <div className="mx-5 mt-4 rounded-lg border border-yellow-400/40 bg-yellow-400/5 px-3 py-3 space-y-2">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-yellow-700 dark:text-yellow-400 shrink-0" />
              <p className="text-xs font-medium text-yellow-700 dark:text-yellow-400">
                {duplicateCount === 1
                  ? "A transaction with the same date, account, description, and amount already exists."
                  : `${duplicateCount} transactions with identical details already exist.`}
              </p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={dismissDuplicate}>
                Go back
              </Button>
              <Button size="sm" onClick={forceAdd} disabled={isPending}>
                {isPending ? "Adding…" : "Add anyway"}
              </Button>
            </div>
          </div>
        )}

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
                placeholder="-42.00"
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
              placeholder="e.g. Whole Foods"
            />
          </Field>

          <Field label="Account" error={errors.accountName?.message}>
            <input
              type="text"
              {...register("accountName")}
              className={InputClass(!!errors.accountName)}
              placeholder="e.g. Chase Checking"
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

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Adding…" : "Add Transaction"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
