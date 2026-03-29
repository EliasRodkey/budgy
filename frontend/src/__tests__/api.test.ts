import { describe, expect, it } from "vitest";
import { getAISummary } from "../api/ai";
import { getMonthlySummary } from "../api/summary";
import { assignCategory, getFlaggedTransactions } from "../api/transactions";
import { mockAISummary, mockMonthlySummaries } from "./fixtures";

describe("getMonthlySummary", () => {
  it("returns the summary for an exact month match", async () => {
    const result = await getMonthlySummary("2025-03");
    expect(result.month).toBe("2025-03");
    expect(result.totalIncome).toBe(3800);
    expect(result.byCategory.length).toBeGreaterThan(0);
  });

  it("falls back to the latest month when the requested month is not in mock data", async () => {
    const result = await getMonthlySummary("2099-01");
    const latestMonth = mockMonthlySummaries[mockMonthlySummaries.length - 1].month;
    expect(result.month).toBe(latestMonth);
  });

  it("returns a MonthlySummary with all required fields", async () => {
    const result = await getMonthlySummary("2025-01");
    expect(typeof result.month).toBe("string");
    expect(typeof result.totalIncome).toBe("number");
    expect(typeof result.totalExpenses).toBe("number");
    expect(typeof result.net).toBe("number");
    expect(Array.isArray(result.byCategory)).toBe(true);
  });

  it("net equals totalIncome minus totalExpenses", async () => {
    const result = await getMonthlySummary("2025-03");
    expect(result.net).toBeCloseTo(result.totalIncome - result.totalExpenses, 2);
  });
});

describe("getAISummary", () => {
  it("returns an AISummary with all required fields", async () => {
    const result = await getAISummary("2025-03");
    expect(typeof result.generatedAt).toBe("string");
    expect(typeof result.recap).toBe("string");
    expect(Array.isArray(result.anomalies)).toBe(true);
    expect(Array.isArray(result.suggestions)).toBe(true);
  });

  it("recap is non-empty", async () => {
    const result = await getAISummary("2025-03");
    expect(result.recap.length).toBeGreaterThan(0);
  });

  it("matches the mock AI summary shape", async () => {
    const result = await getAISummary("2025-03");
    expect(result.recap).toBe(mockAISummary.recap);
    expect(result.anomalies).toEqual(mockAISummary.anomalies);
    expect(result.suggestions).toEqual(mockAISummary.suggestions);
  });
});

describe("getFlaggedTransactions", () => {
  it("returns only flagged transactions", async () => {
    const result = await getFlaggedTransactions();
    expect(result.length).toBeGreaterThan(0);
    for (const tx of result) {
      expect(tx.isFlagged).toBe(true);
    }
  });

  it("each transaction has required fields", async () => {
    const result = await getFlaggedTransactions();
    for (const tx of result) {
      expect(typeof tx.id).toBe("string");
      expect(typeof tx.date).toBe("string");
      expect(typeof tx.amount).toBe("number");
    }
  });
});

describe("assignCategory", () => {
  it("returns an updated transaction with the new category and isFlagged=false", async () => {
    const flagged = await getFlaggedTransactions();
    const target = flagged[0];
    const result = await assignCategory(target.id, "Food & drink", "Groceries");
    expect(result.id).toBe(target.id);
    expect(result.primaryCategory).toBe("Food & drink");
    expect(result.detailedCategory).toBe("Groceries");
    expect(result.isFlagged).toBe(false);
  });

  it("throws when given a non-existent transaction ID", async () => {
    await expect(assignCategory("does-not-exist", "Other", "Other")).rejects.toThrow();
  });
});
