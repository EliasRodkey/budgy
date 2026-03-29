import { useQuery } from "@tanstack/react-query";
import { getAISummary } from "../api/ai";
import type { AISummary } from "../types";

export function useAISummary(month: string) {
  return useQuery<AISummary, Error>({
    queryKey: ["aiSummary", month],
    queryFn: () => getAISummary(month),
    staleTime: Infinity, // Don't auto-refetch; user triggers regenerate manually
  });
}
