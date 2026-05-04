import { useQuery } from "@tanstack/react-query";
import { getFlaggedTransactions } from "../api/transactions";
import type { Transaction } from "../types";

export function useFlaggedTransactions() {
  return useQuery<Transaction[], Error>({
    queryKey: ["flaggedTransactions"],
    queryFn: getFlaggedTransactions,
  });
}
