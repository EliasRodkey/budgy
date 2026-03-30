export const NON_SPENDING_CATEGORIES = new Set([
  "Income",
  "Transfers",
  "Investments",
]);

// Fixed color assignment per spending category — deterministic, shared between donut slices and card dots
export const CATEGORY_COLORS: Record<string, string> = {
  "Food & drink":          "#6366f1", // indigo
  "Shopping":              "#f59e0b", // amber
  "Housing & utilities":   "#10b981", // emerald
  "Health & wellness":     "#f43f5e", // rose
  "Transportation":        "#3b82f6", // blue
  "Entertainment":         "#8b5cf6", // violet
  "Travel":                "#ec4899", // pink
  "Services":              "#14b8a6", // teal
  "Debt payments":         "#f97316", // orange
  "Insurance":             "#84cc16", // lime
  "Government & charity":  "#06b6d4", // cyan
  "Bank fees":             "#a78bfa", // purple
  "Other":                 "#94a3b8", // slate
};
