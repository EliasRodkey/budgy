import { useQuery } from "@tanstack/react-query";
import { checkDirtyMonths, getAvailableYears, getMonthlySummary } from "../api/summary";
import type { DirtyStatusResponse } from "../api/summary";
import type { MonthlySummary } from "../types";

export function useSummary(month: string) {
  return useQuery<MonthlySummary | null, Error>({
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

export function useAvailableYears() {
  return useQuery<number[], Error>({
    queryKey: ["summaries", "years"],
    queryFn: getAvailableYears,
    staleTime: Infinity,
  });
}
