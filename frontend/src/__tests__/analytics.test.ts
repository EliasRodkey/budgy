import { describe, expect, it } from "vitest";
import {
  getAnalytics,
  MOCK_DEFAULT_DATE_FROM,
  MOCK_DEFAULT_DATE_TO,
} from "../api/analytics";
import { mockAnalyticsSeries, mockMonthlySummaries } from "./fixtures";

describe("getAnalytics", () => {
  it("returns series and incomeExpenses for the full mock range", async () => {
    const result = await getAnalytics({
      dateFrom: MOCK_DEFAULT_DATE_FROM,
      dateTo: MOCK_DEFAULT_DATE_TO,
    });
    expect(result.series.labels).toEqual(mockAnalyticsSeries.labels);
    expect(result.incomeExpenses.length).toBe(mockMonthlySummaries.length);
  });

  it("filters labels to the requested date range", async () => {
    const result = await getAnalytics({
      dateFrom: "2025-01",
      dateTo: "2025-03",
    });
    expect(result.series.labels).toEqual(["2025-01", "2025-02", "2025-03"]);
  });

  it("each dataset values array length matches filtered labels length", async () => {
    const result = await getAnalytics({ dateFrom: "2024-11", dateTo: "2025-02" });
    const expectedLength = result.series.labels.length;
    for (const ds of result.series.datasets) {
      expect(ds.values).toHaveLength(expectedLength);
    }
  });

  it("drops categories with all-zero values in the requested range", async () => {
    // "2025-01" to "2025-01" — only categories with a non-zero value in that month survive
    const result = await getAnalytics({ dateFrom: "2025-01", dateTo: "2025-01" });
    for (const ds of result.series.datasets) {
      expect(ds.values.some((v) => v > 0)).toBe(true);
    }
  });

  it("incomeExpenses months match the filtered date range", async () => {
    const result = await getAnalytics({ dateFrom: "2025-01", dateTo: "2025-03" });
    const months = result.incomeExpenses.map((r) => r.month);
    expect(months).toEqual(["2025-01", "2025-02", "2025-03"]);
  });

  it("each incomeExpenses row has income, expenses, and net", async () => {
    const result = await getAnalytics({
      dateFrom: MOCK_DEFAULT_DATE_FROM,
      dateTo: MOCK_DEFAULT_DATE_TO,
    });
    for (const row of result.incomeExpenses) {
      expect(typeof row.income).toBe("number");
      expect(typeof row.expenses).toBe("number");
      expect(typeof row.net).toBe("number");
      expect(row.net).toBeCloseTo(row.income - row.expenses, 2);
    }
  });

  it("returns empty series and incomeExpenses for an out-of-range query", async () => {
    const result = await getAnalytics({ dateFrom: "2030-01", dateTo: "2030-06" });
    expect(result.series.labels).toHaveLength(0);
    expect(result.incomeExpenses).toHaveLength(0);
  });

  it("series datasets contain required fields", async () => {
    const result = await getAnalytics({
      dateFrom: MOCK_DEFAULT_DATE_FROM,
      dateTo: MOCK_DEFAULT_DATE_TO,
    });
    for (const ds of result.series.datasets) {
      expect(typeof ds.categoryId).toBe("string");
      expect(typeof ds.categoryName).toBe("string");
      expect(Array.isArray(ds.values)).toBe(true);
    }
  });
});
