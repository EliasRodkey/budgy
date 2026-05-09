import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createBudget,
  createBudgetAssignment,
  deleteBudget,
  deleteBudgetAssignment,
  getBudgetAssignments,
  getBudgets,
  updateBudget,
} from "../api/budgets";

export function useBudgets() {
  return useQuery({
    queryKey: ["budgets"],
    queryFn: getBudgets,
    retry: 1,
    retryDelay: 500,
  });
}

export function useBudgetAssignments() {
  return useQuery({
    queryKey: ["budgets", "assignments"],
    queryFn: getBudgetAssignments,
    retry: 1,
    retryDelay: 500,
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useUpdateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof updateBudget>[1] }) =>
      updateBudget(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useCreateBudgetAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createBudgetAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useDeleteBudgetAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteBudgetAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}
