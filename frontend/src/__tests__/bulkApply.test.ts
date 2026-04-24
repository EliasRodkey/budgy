import { describe, expect, it } from "vitest";
import type { Transaction } from "../types";

// ─── Helpers extracted from Transactions.tsx bulk-apply logic ────────────────
// These replicate the diffing + scope-filtering logic so it can be tested
// without rendering the full page component.

function diffTags(original: string[], updated: string[]): string[] {
  return updated.filter((t) => !original.includes(t));
}

function categoryChanged(
  original: Pick<Transaction, "primaryCategory" | "detailedCategory">,
  updates: Partial<Transaction>,
): boolean {
  return (
    (updates.primaryCategory !== undefined && updates.primaryCategory !== original.primaryCategory) ||
    (updates.detailedCategory !== undefined && updates.detailedCategory !== original.detailedCategory)
  );
}

function filterByScope(
  similar: Transaction[],
  scope: "all" | "no_existing" | "only_this" | "select",
  selectedIds: number[],
  hasTagChange: boolean,
): number[] {
  if (scope === "all") return similar.map((t) => Number(t.id));
  if (scope === "only_this") return [];
  if (scope === "select") return selectedIds;
  // no_existing
  return similar
    .filter((t) =>
      hasTagChange
        ? !(t.tags && t.tags.length > 0)
        : !t.primaryCategory,
    )
    .map((t) => Number(t.id));
}

function makeTx(overrides: Partial<Transaction> = {}): Transaction {
  return {
    id: "1",
    authorizedDate: "2026-01-01",
    postedDate: "2026-01-01",
    status: "Checked",
    accountName: "Chase Sapphire",
    description: "TRADER JOES",
    primaryCategory: "Food & drink",
    detailedCategory: "Groceries",
    amount: -42.5,
    repayment: false,
    exclude: false,
    tags: [],
    ...overrides,
  };
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("diffTags", () => {
  it("returns only newly added tags", () => {
    expect(diffTags(["a"], ["a", "b", "c"])).toEqual(["b", "c"]);
  });

  it("returns empty when no new tags", () => {
    expect(diffTags(["a", "b"], ["a", "b"])).toEqual([]);
  });

  it("handles empty original", () => {
    expect(diffTags([], ["x", "y"])).toEqual(["x", "y"]);
  });

  it("ignores removed tags", () => {
    expect(diffTags(["a", "b"], ["b"])).toEqual([]);
  });
});

describe("categoryChanged", () => {
  const original = makeTx({ primaryCategory: "Food & drink", detailedCategory: "Groceries" });

  it("returns true when primaryCategory changes", () => {
    expect(categoryChanged(original, { primaryCategory: "Shopping" })).toBe(true);
  });

  it("returns true when detailedCategory changes", () => {
    expect(categoryChanged(original, { detailedCategory: "Online shopping" })).toBe(true);
  });

  it("returns false when same primaryCategory provided", () => {
    expect(categoryChanged(original, { primaryCategory: "Food & drink" })).toBe(false);
  });

  it("returns false when neither field is in updates", () => {
    expect(categoryChanged(original, { amount: -10 })).toBe(false);
  });

  it("returns false when both fields unchanged", () => {
    expect(categoryChanged(original, {
      primaryCategory: "Food & drink",
      detailedCategory: "Groceries",
    })).toBe(false);
  });
});

describe("filterByScope", () => {
  const similar: Transaction[] = [
    makeTx({ id: "10", tags: [] }),
    makeTx({ id: "11", tags: ["existing"] }),
    makeTx({ id: "12", tags: [] }),
  ];

  it("all: returns every id", () => {
    expect(filterByScope(similar, "all", [], true)).toEqual([10, 11, 12]);
  });

  it("only_this: returns empty", () => {
    expect(filterByScope(similar, "only_this", [], true)).toEqual([]);
  });

  it("select: returns provided ids", () => {
    expect(filterByScope(similar, "select", [10, 12], true)).toEqual([10, 12]);
  });

  it("no_existing (tag change): excludes transactions that already have tags", () => {
    const result = filterByScope(similar, "no_existing", [], true);
    expect(result).toEqual([10, 12]); // id 11 has existing tags
  });

  it("no_existing (category change): excludes transactions that already have a category", () => {
    const withoutCategory = similar.map((t, i) =>
      i === 1 ? { ...t, primaryCategory: "" } : t,
    );
    const result = filterByScope(withoutCategory, "no_existing", [], false);
    expect(result).toContain(11); // only the one with no primaryCategory
  });
});
