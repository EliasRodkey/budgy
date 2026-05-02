import { Button } from "@/components/ui/button";
import { importTransactions, pollJobUntilDone, type ImportResult, type UploadJobResponse } from "@/api/transactions";
import { planCSV } from "@/api/ai";
import type { NormalizationPlan } from "@/types";
import { MappingReviewPanel } from "./MappingReviewPanel";
import { CheckCircle, ChevronDown, Upload, X, XCircle } from "lucide-react";
import Papa from "papaparse";
import { useRef, useState } from "react";

type Stage = "pick" | "analyzing" | "review" | "importing" | "result";

interface CSVUploadModalProps {
  onClose: () => void;
}

// Budgy field keys that are required for import
const REQUIRED_FIELDS = ["primary_category", "description", "authorized_date", "amount"];

function friendlyErrorMessage(raw: string | undefined): string {
  if (!raw) return "Check that your file is a valid CSV and try again.";
  const lower = raw.toLowerCase();
  if (lower.includes("unmapped_required") || lower.includes("required column") || lower.includes("required field"))
    return "One or more required columns (Date, Description, Amount, Category) couldn't be matched. Go back to review and assign them manually.";
  if (lower.includes("transformvalidationerror") || lower.includes("transform") || lower.includes("amount column"))
    return "The amount column couldn't be processed. Check that it contains valid numbers and the sign convention is correct.";
  if (lower.includes("anthropic") || lower.includes("api key") || lower.includes("credit"))
    return "The AI analysis service is unavailable. Check your API key configuration and try again.";
  if (lower.includes("unicode") || lower.includes("decode") || lower.includes("encoding"))
    return "The file encoding couldn't be read. Try saving your CSV as UTF-8 and importing again.";
  return "Something went wrong processing your file. Try again or contact support.";
}

function buildFieldMappings(columnMap: NormalizationPlan["column_map"]): Record<string, string | null> {
  // Invert column_map: rawHeader → budgyField  becomes  budgyField → rawHeader
  const mappings: Record<string, string | null> = {
    primary_category: null,
    description: null,
    date: null,
    amount: null,
    detailed_category: null,
    account_name: null,
    authorized_date: null,
    status: null,
    notes: null,
    tags: null,
  };
  for (const [rawHeader, budgyField] of Object.entries(columnMap)) {
    if (budgyField && budgyField in mappings) {
      mappings[budgyField] = rawHeader;
    }
  }
  return mappings;
}

function reconstructColumnMap(fieldMappings: Record<string, string | null>): Record<string, string | null> {
  // Re-invert back to rawHeader → budgyField for the backend
  const columnMap: Record<string, string | null> = {};
  for (const [budgyField, rawHeader] of Object.entries(fieldMappings)) {
    if (rawHeader) {
      columnMap[rawHeader] = budgyField;
    }
  }
  return columnMap;
}

export function CSVUploadModal({ onClose }: CSVUploadModalProps) {
  const [stage, setStage] = useState<Stage>("pick");
  const [file, setFile] = useState<File | null>(null);
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [plan, setPlan] = useState<NormalizationPlan | null>(null);
  const [fieldMappings, setFieldMappings] = useState<Record<string, string | null>>({});
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [formatOpen, setFormatOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function resetTopick() {
    setFile(null);
    setCsvHeaders([]);
    setPlan(null);
    setFieldMappings({});
    setAnalysisError(null);
    if (inputRef.current) inputRef.current.value = "";
    setStage("pick");
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setAnalysisError(null);
    setFile(selected);

    Papa.parse<Record<string, string>>(selected, {
      header: true,
      skipEmptyLines: true,
      preview: 1,
      complete: async (res) => {
        if (res.errors.length > 0) {
          setAnalysisError(res.errors[0].message);
          return;
        }
        const headers = res.meta.fields ?? [];
        setCsvHeaders(headers);
        setStage("analyzing");

        try {
          const receivedPlan = await planCSV(selected);
          setPlan(receivedPlan);

          // Fast path: empty maps mean the CSV is already valid — skip review
          const isAlreadyValid =
            Object.keys(receivedPlan.column_map).length === 0 &&
            Object.keys(receivedPlan.category_map).length === 0;

          if (isAlreadyValid) {
            setStage("importing");
            const job: UploadJobResponse = await importTransactions(selected);
            const importResult = await pollJobUntilDone(job.jobId);
            setResult(importResult);
            setStage("result");
          } else {
            setFieldMappings(buildFieldMappings(receivedPlan.column_map));
            setStage("review");
          }
        } catch (err) {
          setAnalysisError(err instanceof Error ? err.message : "Analysis failed. Please try again.");
          resetToPickKeepError(err instanceof Error ? err.message : "Analysis failed. Please try again.");
        }
      },
      error: (err) => {
        setAnalysisError(err.message);
      },
    });
  }

  function resetToPickKeepError(errorMsg: string) {
    setFile(null);
    setCsvHeaders([]);
    setPlan(null);
    setFieldMappings({});
    if (inputRef.current) inputRef.current.value = "";
    setAnalysisError(errorMsg);
    setStage("pick");
  }

  async function handleApproveAndImport() {
    if (!file || !plan) return;
    setStage("importing");
    try {
      const approvedPlan: NormalizationPlan = {
        ...plan,
        column_map: reconstructColumnMap(fieldMappings),
      };
      const job: UploadJobResponse = await importTransactions(file, approvedPlan);
      const importResult = await pollJobUntilDone(job.jobId);
      setResult(importResult);
      setStage("result");
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "Import failed. Please try again.");
      setStage("review");
    }
  }

  const mappedValues = Object.values(fieldMappings).filter(Boolean) as string[];
  const hasDuplicateMappings = mappedValues.length !== new Set(mappedValues).size;
  const canApprove =
    !hasDuplicateMappings &&
    REQUIRED_FIELDS.every(
      (f) => fieldMappings[f] !== null && fieldMappings[f] !== undefined && fieldMappings[f] !== ""
    );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border shrink-0">
          <h2 className="text-sm font-semibold">Import CSV</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4">

          {/* Pick stage */}
          {stage === "pick" && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Select a CSV file to import transactions. The AI will analyze your columns and categories before import.
              </p>
              {analysisError && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                  {analysisError}
                </div>
              )}
              <button
                onClick={() => inputRef.current?.click()}
                className="w-full rounded-xl border-2 border-dashed border-border hover:border-ring transition-colors py-12 flex flex-col items-center gap-3 text-muted-foreground hover:text-foreground"
              >
                <Upload size={24} />
                <span className="text-sm font-medium">Click to choose a CSV file</span>
                <span className="text-xs">or drag and drop here</span>
              </button>
              <input
                ref={inputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileChange}
              />

              {/* Expected Format collapsible */}
              <div className="rounded-lg border border-border overflow-hidden">
                <button
                  onClick={() => setFormatOpen((o) => !o)}
                  className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/30 transition-colors"
                >
                  Expected Format
                  <ChevronDown
                    size={14}
                    className={`transition-transform duration-200 ${formatOpen ? "rotate-180" : ""}`}
                  />
                </button>
                {formatOpen && (
                  <div className="px-4 pb-4 space-y-4 border-t border-border">
                    <div className="space-y-2 pt-3">
                      <p className="text-xs font-medium text-foreground">Required columns</p>
                      <div className="rounded-md border border-border overflow-hidden">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="bg-muted/30 border-b border-border">
                              <th className="py-2 px-3 text-left font-medium text-muted-foreground">Column</th>
                              <th className="py-2 px-3 text-left font-medium text-muted-foreground">Type</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b border-border">
                              <td className="py-2 px-3 font-medium">Primary Category</td>
                              <td className="py-2 px-3 text-muted-foreground">text</td>
                            </tr>
                            <tr className="border-b border-border">
                              <td className="py-2 px-3 font-medium">Description</td>
                              <td className="py-2 px-3 text-muted-foreground">text</td>
                            </tr>
                            <tr className="border-b border-border">
                              <td className="py-2 px-3 font-medium">Date</td>
                              <td className="py-2 px-3 text-muted-foreground">YYYY-MM-DD or MM/DD/YYYY</td>
                            </tr>
                            <tr>
                              <td className="py-2 px-3 font-medium">Amount</td>
                              <td className="py-2 px-3 text-muted-foreground">number (negative = expense, e.g. -24.99)</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs font-medium text-foreground">Optional columns</p>
                      <p className="text-xs text-muted-foreground">
                        Detailed Category, Account Name, Authorized Date, Status, Notes, Tags
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs font-medium text-foreground">Amount convention</p>
                      <p className="text-xs text-muted-foreground">
                        Negative values are expenses (e.g. <span className="font-mono">-87.43</span>).
                        Positive values are income (e.g. <span className="font-mono">3800.00</span>).
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs font-medium text-foreground">Example row</p>
                      <div className="rounded-md border border-border overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="bg-muted/30 border-b border-border">
                              <th className="py-2 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">Primary Category</th>
                              <th className="py-2 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">Description</th>
                              <th className="py-2 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">Date</th>
                              <th className="py-2 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td className="py-2 px-3 whitespace-nowrap">Food &amp; drink</td>
                              <td className="py-2 px-3 whitespace-nowrap">Costco Wholesale</td>
                              <td className="py-2 px-3 whitespace-nowrap font-mono">2024-10-15</td>
                              <td className="py-2 px-3 whitespace-nowrap font-mono">-143.27</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analyzing stage */}
          {stage === "analyzing" && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className="size-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              <p className="text-sm text-muted-foreground">Analyzing CSV structure…</p>
              <p className="text-xs text-muted-foreground">{file?.name}</p>
            </div>
          )}

          {/* Review stage */}
          {stage === "review" && plan && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Review Mappings</p>
                  <p className="text-xs text-muted-foreground">{file?.name}</p>
                </div>
              </div>
              {analysisError && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                  {analysisError}
                </div>
              )}
              <MappingReviewPanel
                plan={plan}
                csvHeaders={csvHeaders}
                fieldMappings={fieldMappings}
                onMappingsChange={setFieldMappings}
              />
            </div>
          )}

          {/* Importing stage */}
          {stage === "importing" && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className="size-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              <p className="text-sm text-muted-foreground">Importing transactions…</p>
            </div>
          )}

          {/* Result stage */}
          {stage === "result" && result && (
            <div className="space-y-4">
              {result.jobFailed ? (
                <div className="flex items-center gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4">
                  <XCircle size={20} className="text-destructive shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-destructive">Import failed</p>
                    <p className="text-xs text-muted-foreground">
                      {friendlyErrorMessage(result.errorMessage)}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-4">
                  <CheckCircle size={20} className="text-green-500 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">Import complete</p>
                    <p className="text-xs text-muted-foreground">
                      {result.imported} transaction{result.imported !== 1 ? "s" : ""} imported successfully
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-5 border-t border-border shrink-0">
          {stage === "result" && (
            <Button onClick={onClose}>Done</Button>
          )}
          {stage === "review" && (
            <>
              {hasDuplicateMappings && (
                <p className="text-xs text-destructive self-center mr-auto">Each CSV column can only be used once.</p>
              )}
              <Button variant="outline" onClick={resetToPickKeepError.bind(null, "")}>Cancel</Button>
              <Button onClick={handleApproveAndImport} disabled={!canApprove}>
                Approve &amp; Import
              </Button>
            </>
          )}
          {stage === "analyzing" && (
            <Button variant="outline" onClick={resetToPickKeepError.bind(null, "")}>Cancel</Button>
          )}
          {stage === "pick" && (
            <Button variant="outline" onClick={onClose}>Cancel</Button>
          )}
        </div>
      </div>
    </div>
  );
}
