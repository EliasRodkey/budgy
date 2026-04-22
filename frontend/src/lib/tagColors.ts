// Same palette as CATEGORY_COLORS — deterministic per tag name via char-code hash
const TAG_PALETTE = [
  "#6366f1", // indigo
  "#f59e0b", // amber
  "#10b981", // emerald
  "#f43f5e", // rose
  "#3b82f6", // blue
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#14b8a6", // teal
  "#f97316", // orange
  "#84cc16", // lime
  "#06b6d4", // cyan
  "#a78bfa", // purple
];

export function getTagColor(tag: string): string {
  const hash = [...tag].reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return TAG_PALETTE[hash % TAG_PALETTE.length];
}

/** Returns inline style props for a tag pill (light background + matching text). */
export function tagPillStyle(tag: string): React.CSSProperties {
  const color = getTagColor(tag);
  return {
    backgroundColor: `${color}22`, // ~13% opacity
    color,
    borderColor: `${color}44`,
  };
}
