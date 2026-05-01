import type { NormalizationPlan } from "@/types";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";

interface MappingReviewPanelProps {
  plan: NormalizationPlan;
  csvHeaders: string[];
  fieldMappings: Record<string, string | null>; // budgyField → csvHeader | null
  onMappingsChange: (updated: Record<string, string | null>) => void;
}

const BUDGY_FIELDS = [
  { key: "primary_category", label: "Primary Category", required: true,  tooltip: "Main spending category (e.g. Food & drink, Transportation)" },
  { key: "description",      label: "Description",       required: true,  tooltip: "Merchant or transaction description" },
  { key: "date",             label: "Date",              required: true,  tooltip: "Posted date — YYYY-MM-DD or MM/DD/YYYY" },
  { key: "amount",           label: "Amount",            required: true,  tooltip: "Transaction amount — negative is expense, positive is income" },
  { key: "detailed_category",label: "Detailed Category", required: false, tooltip: "Subcategory within the primary category" },
  { key: "account_name",     label: "Account Name",      required: false, tooltip: "Account or institution name" },
  { key: "authorized_date",  label: "Authorized Date",   required: false, tooltip: "Authorization date if different from posted date" },
  { key: "status",           label: "Status",            required: false, tooltip: "Transaction status" },
  { key: "notes",            label: "Notes",             required: false, tooltip: "Personal notes (max 300 characters)" },
  { key: "tags",             label: "Tags",              required: false, tooltip: "Comma-separated tags for filtering" },
] as const;

const AMOUNT_TRANSFORM_LABELS: Record<NormalizationPlan["amount_transform"], string> = {
  signed:       "Single signed column (negative = expense)",
  invert:       "Inverted — positive values treated as expenses",
  debit_credit: "Separate debit / credit columns",
};

export function MappingReviewPanel({ plan, csvHeaders, fieldMappings, onMappingsChange }: MappingReviewPanelProps) {
  function handleFieldChange(fieldKey: string, value: string) {
    onMappingsChange({ ...fieldMappings, [fieldKey]: value === "" ? null : value });
  }

  const hasCategoryMappings = Object.keys(plan.category_map).length > 0;

  return (
    <TooltipProvider>
      <div className="space-y-5">

        {/* Issues */}
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
        </div>

        {/* Amount transform */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Amount detection:</span>
          <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
            {AMOUNT_TRANSFORM_LABELS[plan.amount_transform]}
          </span>
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
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
