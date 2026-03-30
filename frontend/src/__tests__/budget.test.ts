import { describe, expect, it } from "vitest";
import { getEffectiveBudget } from "../lib/budget";
import type { BudgetAssignment } from "../types";

function makeAssignment(
  id: string,
  budgetId: string,
  effectiveFrom: string,
  note: string | null = null,
): BudgetAssignment {
  return { id, budgetId, effectiveFrom, note };
}

describe("getEffectiveBudget — no assignments", () => {
  it("returns null when the list is empty", () => {
    expect(getEffectiveBudget([], "2025-03")).toBeNull();
  });
});

describe("getEffectiveBudget — single assignment", () => {
  it("returns the assignment when effectiveFrom equals month", () => {
    const a = makeAssignment("a1", "b1", "2025-03");
    expect(getEffectiveBudget([a], "2025-03")).toEqual(a);
  });

  it("returns the assignment when effectiveFrom is before month", () => {
    const a = makeAssignment("a1", "b1", "2025-01");
    expect(getEffectiveBudget([a], "2025-03")).toEqual(a);
  });

  it("returns null when the single assignment is future-dated", () => {
    const a = makeAssignment("a1", "b1", "2025-06");
    expect(getEffectiveBudget([a], "2025-03")).toBeNull();
  });
});

describe("getEffectiveBudget — exact effectiveFrom match", () => {
  it("prefers the exact-match assignment over an earlier one", () => {
    const earlier = makeAssignment("a1", "b1", "2025-01");
    const exact = makeAssignment("a2", "b2", "2025-03");
    expect(getEffectiveBudget([earlier, exact], "2025-03")).toEqual(exact);
  });
});

describe("getEffectiveBudget — multiple assignments", () => {
  const assignments: BudgetAssignment[] = [
    makeAssignment("a1", "b1", "2024-10"),
    makeAssignment("a2", "b2", "2025-01"),
    makeAssignment("a3", "b1", "2024-12"),
  ];

  it("returns the most recent assignment that is ≤ month", () => {
    // For 2025-03: eligible are 2024-10, 2025-01, 2024-12 → most recent is 2025-01
    expect(getEffectiveBudget(assignments, "2025-03")).toEqual(assignments[1]);
  });

  it("respects the month boundary — returns latest eligible before the query month", () => {
    // For 2024-11: eligible are 2024-10 only (2024-12 and 2025-01 are future)
    expect(getEffectiveBudget(assignments, "2024-11")).toEqual(assignments[0]);
  });

  it("handles exact month matching with multiple candidates", () => {
    // For 2024-12: eligible are 2024-10 and 2024-12 → most recent is 2024-12
    expect(getEffectiveBudget(assignments, "2024-12")).toEqual(assignments[2]);
  });
});

describe("getEffectiveBudget — future-dated assignments", () => {
  it("ignores all future-dated assignments", () => {
    const past = makeAssignment("a1", "b1", "2025-01");
    const future1 = makeAssignment("a2", "b2", "2025-06");
    const future2 = makeAssignment("a3", "b3", "2026-01");
    expect(getEffectiveBudget([past, future1, future2], "2025-03")).toEqual(past);
  });

  it("returns null when all assignments are in the future", () => {
    const future1 = makeAssignment("a1", "b1", "2025-06");
    const future2 = makeAssignment("a2", "b2", "2025-12");
    expect(getEffectiveBudget([future1, future2], "2025-03")).toBeNull();
  });
});

describe("getEffectiveBudget — order independence", () => {
  it("returns the same result regardless of input order", () => {
    const a1 = makeAssignment("a1", "b1", "2024-10");
    const a2 = makeAssignment("a2", "b2", "2025-01");
    const a3 = makeAssignment("a3", "b1", "2024-12");

    const result1 = getEffectiveBudget([a1, a2, a3], "2025-03");
    const result2 = getEffectiveBudget([a3, a1, a2], "2025-03");
    const result3 = getEffectiveBudget([a2, a3, a1], "2025-03");

    expect(result1).toEqual(result2);
    expect(result1).toEqual(result3);
    expect(result1).toEqual(a2);
  });
});
