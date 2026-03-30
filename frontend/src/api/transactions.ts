import type { Transaction } from "../types";
import { mockTransactions } from "../__tests__/fixtures";

const USE_MOCK = true;

export async function getFlaggedTransactions(): Promise<Transaction[]> {
  if (USE_MOCK) {
    return mockTransactions.filter((t) => t.isFlagged);
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/transactions?flagged=true&page_size=100");
  // if (!res.ok) throw new Error("Failed to fetch flagged transactions");
  // const json = await res.json();
  // return json.data as Transaction[];
  throw new Error("Real API not implemented");
}

export async function assignCategory(
  transactionId: string,
  primaryCategory: string,
  detailedCategory: string,
): Promise<Transaction> {
  if (USE_MOCK) {
    const tx = mockTransactions.find((t) => t.id === transactionId);
    if (!tx) throw new Error(`Transaction ${transactionId} not found`);
    return { ...tx, primaryCategory, detailedCategory, isFlagged: false };
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/transactions/${transactionId}`, {
  //   method: "PUT",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ primaryCategory, detailedCategory, isFlagged: false }),
  // });
  // if (!res.ok) throw new Error("Failed to assign category");
  // const json = await res.json();
  // return json.data as Transaction;
  throw new Error("Real API not implemented");
}
