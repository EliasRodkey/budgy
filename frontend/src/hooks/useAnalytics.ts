import { useQuery } from "@tanstack/react-query";
import { getAnalytics, type AnalyticsData, type AnalyticsFilters } from "../api/analytics";

export function useAnalytics(filters: AnalyticsFilters) {
  return useQuery<AnalyticsData, Error>({
    queryKey: ["analytics", filters.dateFrom, filters.dateTo],
    queryFn: () => getAnalytics(filters),
  });
}
