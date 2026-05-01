import { useQuery } from "@tanstack/react-query";
import {
  fetchCategoryMapping,
  getCategories,
  getCategoryDetail,
  getCategoryOverview,
  getSubcategoryDetail,
} from "../api/categories";

export function useCategoryMapping() {
  return useQuery({
    queryKey: ["categoryMapping"],
    queryFn: fetchCategoryMapping,
    staleTime: Infinity,
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });
}

export function useCategoryOverview(month: number | null, year: number) {
  return useQuery({
    queryKey: ["categories", "overview", month, year],
    queryFn: () => getCategoryOverview(month, year),
  });
}

export function useCategoryDetail(primaryCategory: string, month: number | null, year: number) {
  return useQuery({
    queryKey: ["categories", "detail", primaryCategory, month, year],
    queryFn: () => getCategoryDetail(primaryCategory, month, year),
    enabled: !!primaryCategory,
  });
}

export function useSubcategoryDetail(primaryCategory: string, detailedCategory: string, month: number | null, year: number) {
  return useQuery({
    queryKey: ["categories", "subcategory", primaryCategory, detailedCategory, month, year],
    queryFn: () => getSubcategoryDetail(primaryCategory, detailedCategory, month, year),
    enabled: !!primaryCategory && !!detailedCategory,
  });
}
