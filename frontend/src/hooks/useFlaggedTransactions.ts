import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assignCategory, getFlaggedTransactions } from "../api/transactions";
import type { Transaction } from "../types";

export function useFlaggedTransactions() {
  return useQuery<Transaction[], Error>({
    queryKey: ["flaggedTransactions"],
    queryFn: getFlaggedTransactions,
  });
}

export function useAssignCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionId,
      primaryCategory,
      detailedCategory,
    }: {
      transactionId: string;
      primaryCategory: string;
      detailedCategory: string;
    }) => assignCategory(transactionId, primaryCategory, detailedCategory),

    // Optimistic update: remove the transaction from the flagged list immediately
    onMutate: async ({ transactionId }) => {
      await queryClient.cancelQueries({ queryKey: ["flaggedTransactions"] });
      const previous = queryClient.getQueryData<Transaction[]>(["flaggedTransactions"]);
      queryClient.setQueryData<Transaction[]>(["flaggedTransactions"], (old) =>
        old ? old.filter((t) => t.id !== transactionId) : [],
      );
      return { previous };
    },

    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["flaggedTransactions"], context.previous);
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["flaggedTransactions"] });
    },
  });
}
