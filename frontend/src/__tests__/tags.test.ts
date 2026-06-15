import { describe, expect, it } from "vitest";
import { getTagDetail, getTagsOverview } from "../api/tags";

describe("getTagsOverview", () => {
  it("aggregates total spend and transaction count per tag", async () => {
    const tags = await getTagsOverview();
    const groceries = tags.find((t) => t.tagName === "groceries");
    expect(groceries).toBeDefined();
    expect(groceries!.totalSpend).toBeCloseTo(276.39, 2);
    expect(groceries!.transactionCount).toBe(3);
  });

  it("sorts tags by total spend descending", async () => {
    const tags = await getTagsOverview();
    for (let i = 1; i < tags.length; i++) {
      expect(tags[i - 1].totalSpend).toBeGreaterThanOrEqual(tags[i].totalSpend);
    }
  });
});

describe("getTagDetail", () => {
  it("throws a 404-flagged error for an unknown tag", async () => {
    await expect(getTagDetail("not-a-real-tag")).rejects.toMatchObject({ status: 404 });
  });

  it("returns total spend, category breakdown, and transactions for a tag", async () => {
    const detail = await getTagDetail("rent");
    expect(detail.tagName).toBe("rent");
    expect(detail.totalSpend).toBeCloseTo(3000, 2);
    expect(detail.transactionCount).toBe(2);
    expect(detail.transactions).toHaveLength(2);
    expect(detail.categoryBreakdown).toEqual([
      expect.objectContaining({
        categoryName: "Housing & utilities",
        amount: 3000,
        transactionCount: 2,
        avgPerTransaction: 1500,
      }),
    ]);
  });

  it("builds a contiguous, zero-filled monthly spend-over-time series", async () => {
    const detail = await getTagDetail("groceries");
    expect(detail.spendOverTime.map((p) => p.month)).toEqual(["2024-10", "2024-11"]);
    expect(detail.spendOverTime[0].amount).toBeCloseTo(200.07, 2);
    expect(detail.spendOverTime[1].amount).toBeCloseTo(76.32, 2);
  });

  it("sorts transactions newest first", async () => {
    const detail = await getTagDetail("rent");
    const dates = detail.transactions.map((t) => t.authorizedDate);
    expect(dates).toEqual([...dates].sort().reverse());
  });
});
