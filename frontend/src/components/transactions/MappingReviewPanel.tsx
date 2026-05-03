import type { NormalizationPlan } from "@/types";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";

interface MappingReviewPanelProps {
  plan: NormalizationPlan;
  csvHeaders: string[];
  fieldMappings: Record<string, string | null>; // budgyField → csvHeader | null
  onMappingsChange: (updated: Record<string, string | null>) => void;
  onAmountTransformChange: (transform: NormalizationPlan["amount_transform"]) => void;
  onDebitColumnChange: (col: string | null) => void;
  onCreditColumnChange: (col: string | null) => void;
}

const BUDGY_FIELDS = [
  { key: "primary_category", label: "Primary Category", required: true,  tooltip: "Main spending category (e.g. Food & drink, Transportation)" },
  { key: "description",      label: "Description",       required: true,  tooltip: "Merchant or transaction description" },
  { key: "authorized_date",  label: "Date",              required: true,  tooltip: "Transaction date — YYYY-MM-DD or MM/DD/YYYY" },
  { key: "amount",           label: "Amount",            required: true,  tooltip: "Transaction amount — negative is expense, positive is income" },
  { key: "detailed_category",label: "Detailed Category", required: false, tooltip: "Subcategory within the primary category" },
  { key: "account_name",     label: "Account Name",      required: false, tooltip: "Account or institution name" },
  { key: "posted_date",      label: "Posted Date",        required: false, tooltip: "Posted date if different from transaction date" },
  { key: "status",           label: "Status",            required: false, tooltip: "Transaction status" },
  { key: "notes",            label: "Notes",             required: false, tooltip: "Personal notes (max 300 characters)" },
  { key: "tags",             label: "Tags",              required: false, tooltip: "Comma-separated tags for filtering" },
] as const;

const AMOUNT_TRANSFORM_OPTIONS: { value: NormalizationPlan["amount_transform"]; label: string }[] = [
  { value: "expense_negative", label: "Expenses are negative (standard)" },
  { value: "expense_positive", label: "Expenses are positive (will be negated)" },
  { value: "debit_credit",     label: "Separate debit / credit columns" },
];

function ReasoningNote({ text }: { text: string | null }) {
  if (!text) return null;
  return (
    <p className="text-xs text-muted-foreground italic mt-1">{text}</p>
  );
}

export function MappingReviewPanel({
  plan,
  csvHeaders,
  fieldMappings,
  onMappingsChange,
  onAmountTransformChange,
  onDebitColumnChange,
  onCreditColumnChange,
}: MappingReviewPanelProps) {
  function handleFieldChange(fieldKey: string, value: string) {
    onMappingsChange({ ...fieldMappings, [fieldKey]: value === "" ? null : value });
  }

  const hasCategoryMappings = Object.keys(plan.category_map).length > 0;

  return (
    <TooltipProvider>
      <div className="space-y-5">

        {/* Issues — structural errors only */}
        {plan.issues.length > 0 && (
          <div className="space-y-2">
            {plan.issues.map((issue, i) => (
              <div key={i} className="rounded-lg border border-yellow-400/40 bg-yellow-400/5 p-3 text-xs text-yellow-700 dark:text-yellow-400">
                {issue}
              </div>
            ))}
          </div>
        )}

        {/* Column mappings */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-foreground">Column Mappings</p>
          <p className="text-xs text-muted-foreground">
            Each Budgy field is pre-filled with the AI's best match. Required fields must be assigned to continue.
          </p>
          <div className="rounded-lg border border-border overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-muted/30 border-b border-border">
                  <th className="py-2 px-3 text-left font-medium text-muted-foreground w-1/2">Budgy Field</th>
                  <th className="py-2 px-3 text-left font-medium text-muted-foreground w-1/2">Your CSV Column</th>
                </tr>
              </thead>
              <tbody>
                {BUDGY_FIELDS.map((field, i) => {
                  const mapped = fieldMappings[field.key];
                  const isUnassigned = mapped === null || mapped === "";
                  const isInvalid = field.required && isUnassigned;
                  return (
                    <tr
                      key={field.key}
                      className={`border-b border-border last:border-0 ${isInvalid ? "bg-destructive/5" : ""}`}
                    >
                      <td className={`py-2 px-3 ${i === 0 ? "" : ""}`}>
                        <div className="flex items-center gap-1.5">
                          <span className={field.required ? "font-medium" : "text-muted-foreground"}>
                            {field.label}
                          </span>
                          {field.required && (
                            <span className="text-destructive font-medium">*</span>
                          )}
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button className="text-muted-foreground hover:text-foreground transition-colors" type="button">
                                <HelpCircle size={11} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="right">
                              {field.tooltip}
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </td>
                      <td className="py-1.5 px-3">
                        <select
                          value={mapped ?? ""}
                          onChange={(e) => handleFieldChange(field.key, e.target.value)}
                          className={`w-full h-7 rounded-md border px-2 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-ring ${
                            isInvalid ? "border-destructive/60" : "border-border"
                          }`}
                        >
                          <option value="">
                            {field.required ? "— select a column —" : "(none)"}
                          </option>
                          {csvHeaders.map((h) => (
                            <option key={h} value={h}>{h}</option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-muted-foreground">
            <span className="text-destructive">*</span> Required
          </p>
          <ReasoningNote text={plan.column_map_reasoning} />
        </div>

        {/* Amount transform */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-foreground">Amount Sign Convention</p>
          <select
            value={plan.amount_transform}
            onChange={(e) => onAmountTransformChange(e.target.value as NormalizationPlan["amount_transform"])}
            className="w-full h-8 rounded-md border border-border px-2 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {AMOUNT_TRANSFORM_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <ReasoningNote text={plan.amount_transform_reasoning} />

          {/* Debit/credit column pickers — shown only when debit_credit is selected */}
          {plan.amount_transform === "debit_credit" && (
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Debit column</p>
                <select
                  value={plan.debit_column ?? ""}
                  onChange={(e) => onDebitColumnChange(e.target.value || null)}
                  className="w-full h-7 rounded-md border border-border px-2 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">— select —</option>
                  {csvHeaders.map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Credit column</p>
                <select
                  value={plan.credit_column ?? ""}
                  onChange={(e) => onCreditColumnChange(e.target.value || null)}
                  className="w-full h-7 rounded-md border border-border px-2 text-xs bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">— select —</option>
                  {csvHeaders.map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Category mappings */}
        {hasCategoryMappings && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-foreground">Category Mappings</p>
            <p className="text-xs text-muted-foreground">
              These category values from your CSV will be normalized automatically.
            </p>
            <div className="rounded-lg border border-border overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-muted/30 border-b border-border">
                    <th className="py-2 px-3 text-left font-medium text-muted-foreground">Your Category</th>
                    <th className="py-2 px-3 text-left font-medium text-muted-foreground">Maps To</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(plan.category_map).map(([raw, mapped], i) => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="py-2 px-3 text-muted-foreground">{raw}</td>
                      <td className="py-2 px-3">
                        {mapped.primary}
                        {mapped.detailed && (
                          <span className="text-muted-foreground"> / {mapped.detailed}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ReasoningNote text={plan.category_map_reasoning} />
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
