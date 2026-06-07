import { describe, expect, it } from "vitest";
import { getFlagReasons } from "../lib/transactionFlags";
import type { Transaction } from "../types";

const categoryMapping: Record<string, string[]> = {
  "Food & drink": ["Groceries", "Restaurants & bars"],
  Shopping: ["Clothing & accessories", "Electronics"],
};

const baseTx = (overrides: Partial<Transaction> = {}): Transaction => ({
  id: "1",
  authorizedDate: "2024-10-15",
  status: "Unchecked",
  accountName: "Checking",
  description: "Costco Wholesale",
  primaryCategory: "Food & drink",
  detailedCategory: "Groceries",
  amount: -143.27,
  repayment: false,
  exclude: false,
  ...overrides,
});

describe("getFlagReasons — missing fields", () => {
  it("returns no reasons for a complete, valid transaction", () => {
    expect(getFlagReasons(baseTx(), categoryMapping)).toEqual([]);
  });

  it("reports missing description", () => {
    expect(getFlagReasons(baseTx({ description: "" }), categoryMapping)).toContain("Missing description");
  });

  it("reports missing amount", () => {
    expect(getFlagReasons(baseTx({ amount: null as unknown as number }), categoryMapping)).toContain("Missing amount");
  });

  it("reports missing primary category", () => {
    expect(getFlagReasons(baseTx({ primaryCategory: "" }), categoryMapping)).toContain("Missing primary category");
  });

  it("reports missing detailed category", () => {
    expect(getFlagReasons(baseTx({ detailedCategory: "" }), categoryMapping)).toContain("Missing detailed category");
  });
});

describe("getFlagReasons — unrecognised categories", () => {
  it("reports an unrecognised primary category", () => {
    const reasons = getFlagReasons(baseTx({ primaryCategory: "Food and drink" }), categoryMapping);
    expect(reasons).toContain("Unrecognised primary category: 'Food and drink'");
  });

  it("reports an unrecognised detailed category", () => {
    const reasons = getFlagReasons(baseTx({ detailedCategory: "Snacks" }), categoryMapping);
    expect(reasons).toContain("Unrecognised detailed category: 'Snacks'");
  });

  it("does not report unrecognised reasons for empty fields (missing already covers it)", () => {
    const reasons = getFlagReasons(baseTx({ primaryCategory: "" }), categoryMapping);
    expect(reasons.some((r) => r.startsWith("Unrecognised"))).toBe(false);
  });

  it("skips category-validity checks when no mapping is supplied", () => {
    const reasons = getFlagReasons(baseTx({ primaryCategory: "Food and drink" }));
    expect(reasons).toEqual([]);
  });
});
