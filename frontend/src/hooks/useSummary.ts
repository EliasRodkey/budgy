import { useQuery } from "@tanstack/react-query";
import { checkDirtyMonths, getMonthlySummary } from "../api/summary";
import type { DirtyStatusResponse } from "../api/summary";
import type { MonthlySummary } from "../types";

export function useSummary(month: string) {
  return useQuery<MonthlySummary, Error>({
    queryKey: ["summary", month],
    queryFn: () => getMonthlySummary(month),
  });
}

export function useDirtyMonths() {
  return useQuery<DirtyStatusResponse, Error>({
    queryKey: ["summaries", "dirty"],
    queryFn: checkDirtyMonths,
    staleTime: 0,
  });
}
