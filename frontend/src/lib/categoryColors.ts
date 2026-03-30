export const NON_SPENDING_CATEGORIES = new Set([
  "Income",
  "Transfers",
  "Investments",
]);

/** Convert a hex color string to [h, s, l] (h: 0-360, s: 0-100, l: 0-100). */
function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l * 100];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = 0;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
}

/**
 * Generate `count` distinct shades of a base hex color by stepping lightness
 * from ~30% (dark) to ~72% (light) in HSL space.
 */
export function getCategoryShades(baseHex: string, count: number): string[] {
  if (count === 0) return [];
  if (count === 1) return [baseHex];
  const [h, s] = hexToHsl(baseHex);
  const minL = 30;
  const maxL = 72;
  return Array.from({ length: count }, (_, i) => {
    const l = count === 1 ? (minL + maxL) / 2 : minL + (i * (maxL - minL)) / (count - 1);
    return `hsl(${h}, ${s}%, ${Math.round(l)}%)`;
  });
}

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
