import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  bulkUpdateTransactions,
  deleteTransaction,
  getAvailableTags,
  getSimilarTransactions,
  getTransactions,
  importTransactions,
  updateTransaction,
  type BulkUpdatePayload,
  type TransactionFilters,
} from "../api/transactions";

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => getTransactions(filters),
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Parameters<typeof updateTransaction>[1] }) =>
      updateTransaction(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["availableTags"] });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteTransaction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
}

export function useImportTransactions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => importTransactions(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
}

export function useAvailableTags() {
  return useQuery({
    queryKey: ["availableTags"],
    queryFn: getAvailableTags,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSimilarTransactions(
  description: string,
  accountName: string,
  excludeId?: number,
  enabled = true,
) {
  return useQuery({
    queryKey: ["transactions", "similar", description, accountName, excludeId],
    queryFn: () => getSimilarTransactions(description, accountName, excludeId),
    enabled: enabled && !!description && !!accountName,
  });
}

export function useBulkUpdateTransactions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkUpdatePayload) => bulkUpdateTransactions(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["availableTags"] });
    },
  });
}
