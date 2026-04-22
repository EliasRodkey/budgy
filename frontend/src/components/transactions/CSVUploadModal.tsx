import { Button } from "@/components/ui/button";
import { importTransactions, pollJobUntilDone, type ImportResult, type UploadJobResponse } from "@/api/transactions";
import { CheckCircle, Upload, X, XCircle } from "lucide-react";
import Papa from "papaparse";
import { useRef, useState } from "react";

type Stage = "pick" | "preview" | "importing" | "result";

interface CSVUploadModalProps {
  onClose: () => void;
}

interface PreviewRow {
  [key: string]: string;
}


export function CSVUploadModal({ onClose }: CSVUploadModalProps) {
  const [stage, setStage] = useState<Stage>("pick");
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<PreviewRow[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setParseError(null);
    setFile(selected);

    Papa.parse<PreviewRow>(selected, {
      header: true,
      skipEmptyLines: true,
      preview: 10,
      complete: (res) => {
        if (res.errors.length > 0) {
          setParseError(res.errors[0].message);
          return;
        }
        setHeaders(res.meta.fields ?? []);
        setRows(res.data);
        setStage("preview");
      },
      error: (err) => {
        setParseError(err.message);
      },
    });
  }

  async function handleConfirm() {
    if (!file) return;
    setStage("importing");
    try {
      const job: UploadJobResponse = await importTransactions(file);
      const importResult = await pollJobUntilDone(job.jobId);
      setResult(importResult);
      setStage("result");
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "Import failed. Please try again.");
      setStage("preview");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
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
                Select a CSV file to import transactions. You'll get a preview before confirming.
              </p>
              {parseError && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                  {parseError}
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
            </div>
          )}

          {/* Preview stage */}
          {stage === "preview" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Preview — {file?.name}</p>
                <button
                  onClick={() => { setStage("pick"); setFile(null); setRows([]); setHeaders([]); if (inputRef.current) inputRef.current.value = ""; }}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Change file
                </button>
              </div>
              {parseError && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                  {parseError}
                </div>
              )}
              <div className="rounded-lg border border-border overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-muted/30">
                      {headers.map((h) => (
                        <th key={h} className="py-2 px-3 text-left font-medium text-muted-foreground whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={i} className="border-b border-border last:border-0">
                        {headers.map((h) => (
                          <td key={h} className="py-2 px-3 whitespace-nowrap">{row[h]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground">Showing first {rows.length} rows</p>
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
              <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-4">
                <CheckCircle size={20} className="text-green-500 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Import complete</p>
                  <p className="text-xs text-muted-foreground">
                    {result.imported} transaction{result.imported !== 1 ? "s" : ""} imported successfully
                    {result.failed.length > 0 && `, ${result.failed.length} failed`}
                  </p>
                </div>
              </div>

              {result.failed.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <XCircle size={14} className="text-destructive" />
                    <p className="text-xs font-medium text-destructive">Failed rows</p>
                  </div>
                  <div className="rounded-lg border border-border overflow-hidden">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border bg-muted/30">
                          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Row</th>
                          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.failed.map((f) => (
                          <tr key={f.row} className="border-b border-border last:border-0">
                            <td className="py-2 px-3 tabular-nums">{f.row}</td>
                            <td className="py-2 px-3 text-muted-foreground">{f.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
          {stage === "preview" && (
            <>
              <Button variant="outline" onClick={onClose}>Cancel</Button>
              <Button onClick={handleConfirm}>Import</Button>
            </>
          )}
          {stage === "pick" && (
            <Button variant="outline" onClick={onClose}>Cancel</Button>
          )}
        </div>
      </div>
    </div>
  );
}
