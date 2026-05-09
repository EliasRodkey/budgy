import { Button } from "@/components/ui/button";
import { useAvailableYears } from "@/hooks/useSummary";
import { useDateRangeStore } from "@/store/dateRange";
import { RotateCcw } from "lucide-react";
import { useEffect } from "react";

const MONTHS = [
  { value: null, label: "Full Year" },
  { value: 1, label: "January" },
  { value: 2, label: "February" },
  { value: 3, label: "March" },
  { value: 4, label: "April" },
  { value: 5, label: "May" },
  { value: 6, label: "June" },
  { value: 7, label: "July" },
  { value: 8, label: "August" },
  { value: 9, label: "September" },
  { value: 10, label: "October" },
  { value: 11, label: "November" },
  { value: 12, label: "December" },
];

const SELECT_CLS =
  "rounded-md border border-input bg-background px-2 h-8 text-sm focus:outline-none focus:ring-2 focus:ring-ring";

export function DateRangeSelector() {
  const { month, year, setMonth, setYear, reset } = useDateRangeStore();
  const { data: availableYears = [] } = useAvailableYears();

  const currentYear = new Date().getFullYear();
  const years = availableYears.length > 0 ? availableYears : [currentYear];

  useEffect(() => {
    if (availableYears.length > 0 && !availableYears.includes(year)) {
      setYear(availableYears[availableYears.length - 1]);
    }
  }, [availableYears, year, setYear]);

  return (
    <div className="flex items-center gap-2">
      <select
        className={SELECT_CLS}
        value={month ?? ""}
        onChange={(e) =>
          setMonth(e.target.value === "" ? null : Number(e.target.value))
        }
      >
        {MONTHS.map((m) => (
          <option key={String(m.value)} value={m.value ?? ""}>
            {m.label}
          </option>
        ))}
      </select>
      <select
        className={SELECT_CLS}
        value={year}
        onChange={(e) => setYear(Number(e.target.value))}
      >
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
      <Button
        variant="ghost"
        size="sm"
        onClick={reset}
        title="Reset to current month"
        className="h-8 w-8 p-0"
      >
        <RotateCcw size={13} />
      </Button>
    </div>
  );
}
