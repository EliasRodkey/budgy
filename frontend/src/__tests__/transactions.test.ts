import { describe, expect, it } from "vitest";
import {
  deleteTransaction,
  getTransactions,
  importTransactions,
  updateTransaction,
} from "../api/transactions";
import { mockTransactions } from "./fixtures";

// Reset the mutable mock state between tests by re-importing after each test.
// Because the module is cached, we rely on test isolation via order-independent
// assertions against the initial mock dataset where possible.

describe("getTransactions", () => {
  it("returns all transactions when no filters are applied", async () => {
    const result = await getTransactions();
    expect(result.data.length).toBeGreaterThan(0);
    expect(typeof result.total).toBe("number");
    expect(result.page).toBe(1);
    expect(result.pageSize).toBe(20);
  });

  it("paginates correctly", async () => {
    const page1 = await getTransactions({ page: 1, pageSize: 5 });
    const page2 = await getTransactions({ page: 2, pageSize: 5 });
    expect(page1.data.length).toBe(5);
    expect(page2.data.length).toBe(5);
    expect(page1.data[0].id).not.toBe(page2.data[0].id);
  });

  it("last page may have fewer items than pageSize", async () => {
    const all = await getTransactions({ pageSize: 1000 });
    const total = all.total;
    const lastPage = Math.ceil(total / 5);
    const last = await getTransactions({ page: lastPage, pageSize: 5 });
    expect(last.data.length).toBeGreaterThan(0);
    expect(last.data.length).toBeLessThanOrEqual(5);
  });

  it("filters by free-text search on description", async () => {
    const result = await getTransactions({ search: "Whole Foods" });
    expect(result.data.length).toBeGreaterThan(0);
    for (const tx of result.data) {
      const hit =
        tx.description.toLowerCase().includes("whole foods") ||
        tx.account_name.toLowerCase().includes("whole foods");
      expect(hit).toBe(true);
    }
  });

  it("returns empty results for a search that matches nothing", async () => {
    const result = await getTransactions({ search: "zzzzzz-no-match-zzzzzz" });
    expect(result.data.length).toBe(0);
    expect(result.total).toBe(0);
  });

  it("filters by primary category", async () => {
    const result = await getTransactions({ primaryCategory: "Food & drink" });
    expect(result.total).toBeGreaterThan(0);
    for (const tx of result.data) {
      expect(
        tx.primaryCategory === "Food & drink" || tx.detailedCategory === "Food & drink",
      ).toBe(true);
    }
  });

  it("filters by date range", async () => {
    const result = await getTransactions({ dateFrom: "2025-01-01", dateTo: "2025-01-31" });
    for (const tx of result.data) {
      expect(tx.authorizedDate >= "2025-01-01").toBe(true);
      expect(tx.authorizedDate <= "2025-01-31").toBe(true);
    }
  });

  it("sorts by date descending by default", async () => {
    const result = await getTransactions({ sortBy: "date", sortOrder: "desc", pageSize: 100 });
    for (let i = 1; i < result.data.length; i++) {
      expect(result.data[i - 1].authorizedDate >= result.data[i].authorizedDate).toBe(true);
    }
  });

  it("sorts by date ascending", async () => {
    const result = await getTransactions({ sortBy: "date", sortOrder: "asc", pageSize: 100 });
    for (let i = 1; i < result.data.length; i++) {
      expect(result.data[i - 1].authorizedDate <= result.data[i].authorizedDate).toBe(true);
    }
  });

  it("sorts by amount descending", async () => {
    const result = await getTransactions({ sortBy: "amount", sortOrder: "desc", pageSize: 100 });
    for (let i = 1; i < result.data.length; i++) {
      expect(result.data[i - 1].amount >= result.data[i].amount).toBe(true);
    }
  });

  it("total reflects filtered count, not full dataset", async () => {
    const all = await getTransactions();
    const filtered = await getTransactions({ primaryCategory: "Income" });
    expect(filtered.total).toBeLessThan(all.total);
  });

  it("each transaction has all required fields", async () => {
    const result = await getTransactions({ pageSize: 5 });
    for (const tx of result.data) {
      expect(typeof tx.id).toBe("string");
      expect(typeof tx.authorizedDate).toBe("string");
      expect(typeof tx.description).toBe("string");
      expect(typeof tx.account_name).toBe("string");
      expect(typeof tx.amount).toBe("number");
      expect(typeof tx.primaryCategory).toBe("string");
      expect(typeof tx.detailedCategory).toBe("string");
      expect(typeof tx.status).toBe("string");
      expect(typeof tx.exclude).toBe("boolean");
      expect(typeof tx.repayment).toBe("boolean");
    }
  });
});

describe("updateTransaction", () => {
  it("returns the updated transaction with new values", async () => {
    const target = mockTransactions.find((t) => !t.status || t.status !== "Unchecked"); // Find a non-flagged transaction to update
    if (!target) throw new Error("No non-flagged transaction in mock data");
    const result = await updateTransaction(target.id, {
      description: "Updated description",
      primaryCategory: "Other",
    });
    expect(result.id).toBe(target.id);
    expect(result.description).toBe("Updated description");
    expect(result.primaryCategory).toBe("Other");
  });

  it("throws when given a non-existent ID", async () => {
    await expect(updateTransaction("does-not-exist", { description: "x" })).rejects.toThrow();
  });
});

describe("deleteTransaction", () => {
  it("throws when given a non-existent ID", async () => {
    await expect(deleteTransaction("does-not-exist")).rejects.toThrow();
  });
});

describe("importTransactions", () => {
  it("returns an ImportResult with imported count and failed array", async () => {
    const file = new File(["date,description,amount\n2025-01-01,Test,100"], "test.csv", {
      type: "text/csv",
    });
    const result = await importTransactions(file);
    expect(typeof result.imported).toBe("number");
    expect(Array.isArray(result.failed)).toBe(true);
    for (const f of result.failed) {
      expect(typeof f.row).toBe("number");
      expect(typeof f.reason).toBe("string");
    }
  });

  it("mock returns 5 imported and 2 failed rows", async () => {
    const file = new File(["date,description,amount"], "test.csv", { type: "text/csv" });
    const result = await importTransactions(file);
    expect(result.imported).toBe(5);
    expect(result.failed.length).toBe(2);
  });
});
