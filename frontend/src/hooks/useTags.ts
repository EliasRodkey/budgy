import { useQuery } from "@tanstack/react-query";
import { getTagDetail, getTagsOverview } from "../api/tags";

export function useTagsOverview() {
  return useQuery({
    queryKey: ["tags", "overview"],
    queryFn: getTagsOverview,
  });
}

export function useTagDetail(tagName: string) {
  return useQuery({
    queryKey: ["tags", "detail", tagName],
    queryFn: () => getTagDetail(tagName),
    enabled: !!tagName,
  });
}
