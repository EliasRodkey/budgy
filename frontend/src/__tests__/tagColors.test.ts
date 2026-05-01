import { describe, expect, it } from "vitest";
import { getTagColor, tagPillStyle } from "../lib/tagColors";

describe("getTagColor", () => {
  it("returns a hex color string", () => {
    const color = getTagColor("groceries");
    expect(color).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it("is deterministic — same tag always gets same color", () => {
    expect(getTagColor("groceries")).toBe(getTagColor("groceries"));
    expect(getTagColor("travel")).toBe(getTagColor("travel"));
  });

  it("different tags can get different colors", () => {
    const colors = new Set(["groceries", "travel", "dining", "subscriptions", "health"].map(getTagColor));
    // At least some variety — not all the same
    expect(colors.size).toBeGreaterThan(1);
  });

  it("handles empty string without throwing", () => {
    expect(() => getTagColor("")).not.toThrow();
  });

  it("handles single character tags", () => {
    expect(getTagColor("a")).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it("stays within the palette — returns one of the known colors", () => {
    const PALETTE = [
      "#6366f1", "#f59e0b", "#10b981", "#f43f5e",
      "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6",
      "#f97316", "#84cc16", "#06b6d4", "#a78bfa",
    ];
    for (const tag of ["foo", "bar", "baz", "qux", "quux"]) {
      expect(PALETTE).toContain(getTagColor(tag));
    }
  });
});

describe("tagPillStyle", () => {
  it("returns backgroundColor, color, and borderColor", () => {
    const style = tagPillStyle("groceries");
    expect(style).toHaveProperty("backgroundColor");
    expect(style).toHaveProperty("color");
    expect(style).toHaveProperty("borderColor");
  });

  it("backgroundColor uses low opacity hex suffix", () => {
    const style = tagPillStyle("groceries");
    // backgroundColor should be the hex color + 2-char alpha suffix
    expect(style.backgroundColor as string).toMatch(/^#[0-9a-f]{6}[0-9a-f]{2}$/i);
  });

  it("color matches getTagColor output", () => {
    const tag = "travel";
    expect(tagPillStyle(tag).color).toBe(getTagColor(tag));
  });
});
