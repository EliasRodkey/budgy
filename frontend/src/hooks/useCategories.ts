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

export function useCategoryOverview(month: string) {
  return useQuery({
    queryKey: ["categories", "overview", month],
    queryFn: () => getCategoryOverview(month),
  });
}

export function useCategoryDetail(primaryCategory: string) {
  return useQuery({
    queryKey: ["categories", "detail", primaryCategory],
    queryFn: () => getCategoryDetail(primaryCategory),
    enabled: !!primaryCategory,
  });
}

export function useSubcategoryDetail(primaryCategory: string, detailedCategory: string) {
  return useQuery({
    queryKey: ["categories", "subcategory", primaryCategory, detailedCategory],
    queryFn: () => getSubcategoryDetail(primaryCategory, detailedCategory),
    enabled: !!primaryCategory && !!detailedCategory,
  });
}
