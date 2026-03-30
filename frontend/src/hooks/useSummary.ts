import { useQuery } from "@tanstack/react-query";
import { getMonthlySummary } from "../api/summary";
import type { MonthlySummary } from "../types";

export function useSummary(month: string) {
  return useQuery<MonthlySummary, Error>({
    queryKey: ["summary", month],
    queryFn: () => getMonthlySummary(month),
  });
}
