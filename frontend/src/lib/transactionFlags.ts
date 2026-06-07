import type { Transaction } from "@/types";

const MISSING_FIELD_LABELS: Record<string, string> = {
  description: "description",
  amount: "amount",
  authorizedDate: "date",
  primaryCategory: "primary category",
  detailedCategory: "detailed category",
};

/**
 * Builds the list of human-readable reasons a transaction is flagged, distinguishing
 * fields that are missing entirely from ones that hold an unrecognised category value
 * (e.g. mismapped during CSV import). Used by both the flagged list and the edit modal
 * so the messaging stays consistent.
 */
export function getFlagReasons(tx: Transaction, categoryMapping?: Record<string, string[]>): string[] {
  const reasons: string[] = [];
  const checks: Array<[keyof typeof MISSING_FIELD_LABELS, boolean]> = [
    ["description", !tx.description],
    ["amount", tx.amount == null],
    ["authorizedDate", !tx.authorizedDate],
    ["primaryCategory", !tx.primaryCategory],
    ["detailedCategory", !tx.detailedCategory],
  ];
  for (const [key, missing] of checks) {
    if (missing) reasons.push(`Missing ${MISSING_FIELD_LABELS[key]}`);
  }

  if (categoryMapping) {
    const detailedCategories = Object.values(categoryMapping).flat();

    if (tx.primaryCategory && !(tx.primaryCategory in categoryMapping)) {
      reasons.push(`Unrecognised primary category: '${tx.primaryCategory}'`);
    }
    if (tx.detailedCategory && !detailedCategories.includes(tx.detailedCategory)) {
      reasons.push(`Unrecognised detailed category: '${tx.detailedCategory}'`);
    }
  }

  return reasons;
}
