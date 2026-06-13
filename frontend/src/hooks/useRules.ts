import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createRule,
  deleteRule,
  getRuleMatches,
  getRules,
  updateRule,
  type RuleInput,
} from "../api/rules";

export function useRules() {
  return useQuery({
    queryKey: ["rules"],
    queryFn: getRules,
    retry: 1,
    retryDelay: 500,
  });
}

export function useRuleMatches(id: number | undefined) {
  return useQuery({
    queryKey: ["rules", id, "matches"],
    queryFn: () => getRuleMatches(id as number),
    enabled: id !== undefined,
    retry: 1,
    retryDelay: 500,
  });
}

function invalidateRuleQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["rules"] });
  queryClient.invalidateQueries({ queryKey: ["transactions"] });
  queryClient.invalidateQueries({ queryKey: ["summaries", "dirty"] });
}

export function useCreateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRule,
    onSuccess: () => invalidateRuleQueries(queryClient),
  });
}

export function useUpdateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: RuleInput }) => updateRule(id, payload),
    onSuccess: () => invalidateRuleQueries(queryClient),
  });
}

export function useDeleteRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteRule,
    onSuccess: () => invalidateRuleQueries(queryClient),
  });
}
