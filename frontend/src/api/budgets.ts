import type { Budget, BudgetAssignment } from "../types";
import { mockBudgets, mockBudgetAssignments } from "../__tests__/fixtures";

const USE_MOCK = true;

// In-memory mutable copies for mock CRUD operations
let mutableBudgets: Budget[] = [...mockBudgets];
let mutableAssignments: BudgetAssignment[] = [...mockBudgetAssignments];

// ─── Budgets ──────────────────────────────────────────────────────────────────

export async function getBudgets(): Promise<Budget[]> {
  if (USE_MOCK) {
    return [...mutableBudgets];
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/budgets");
  // if (!res.ok) throw new Error("Failed to fetch budgets");
  // const json = await res.json();
  // return json.data as Budget[];
  throw new Error("Real API not implemented");
}

export async function createBudget(
  payload: Omit<Budget, "id" | "dateCreated">,
): Promise<Budget> {
  if (USE_MOCK) {
    const budget: Budget = {
      ...payload,
      note: payload.note ?? null,
      id: `budget-${Date.now()}`,
      dateCreated: new Date().toISOString(),
    };
    mutableBudgets = [...mutableBudgets, budget];
    return budget;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/budgets", {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify(payload),
  // });
  // if (!res.ok) throw new Error("Failed to create budget");
  // const json = await res.json();
  // return json.data as Budget;
  throw new Error("Real API not implemented");
}

export async function updateBudget(
  id: string,
  payload: Partial<Omit<Budget, "id" | "dateCreated">>,
): Promise<Budget> {
  if (USE_MOCK) {
    const idx = mutableBudgets.findIndex((b) => b.id === id);
    if (idx === -1) throw new Error(`Budget ${id} not found`);
    const updated: Budget = { ...mutableBudgets[idx], ...payload };
    mutableBudgets = mutableBudgets.map((b) => (b.id === id ? updated : b));
    return updated;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/budgets/${id}`, {
  //   method: "PUT",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify(payload),
  // });
  // if (!res.ok) throw new Error("Failed to update budget");
  // const json = await res.json();
  // return json.data as Budget;
  throw new Error("Real API not implemented");
}

export async function deleteBudget(id: string): Promise<void> {
  if (USE_MOCK) {
    const idx = mutableBudgets.findIndex((b) => b.id === id);
    if (idx === -1) throw new Error(`Budget ${id} not found`);
    mutableBudgets = mutableBudgets.filter((b) => b.id !== id);
    // Assignments are NOT cascade-deleted — the caller must reassign covered
    // months before deleting a budget that has assignments.
    return;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/budgets/${id}`, { method: "DELETE" });
  // if (!res.ok) throw new Error("Failed to delete budget");
  throw new Error("Real API not implemented");
}

// ─── Budget Assignments ───────────────────────────────────────────────────────

export async function getBudgetAssignments(): Promise<BudgetAssignment[]> {
  if (USE_MOCK) {
    return [...mutableAssignments];
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/budgets/assignments");
  // if (!res.ok) throw new Error("Failed to fetch budget assignments");
  // const json = await res.json();
  // return json.data as BudgetAssignment[];
  throw new Error("Real API not implemented");
}

export async function createBudgetAssignment(
  payload: Omit<BudgetAssignment, "id">,
): Promise<BudgetAssignment> {
  if (USE_MOCK) {
    // Upsert: replace any existing assignment for the same effectiveFrom month
    // so that reassigning the current month always takes effect immediately.
    mutableAssignments = mutableAssignments.filter(
      (a) => a.effectiveFrom !== payload.effectiveFrom,
    );
    const assignment: BudgetAssignment = {
      ...payload,
      id: `assign-${Date.now()}`,
    };
    mutableAssignments = [...mutableAssignments, assignment];
    return assignment;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch("/api/budgets/assignments", {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify(payload),
  // });
  // if (!res.ok) throw new Error("Failed to create budget assignment");
  // const json = await res.json();
  // return json.data as BudgetAssignment;
  throw new Error("Real API not implemented");
}

export async function deleteBudgetAssignment(id: string): Promise<void> {
  if (USE_MOCK) {
    const idx = mutableAssignments.findIndex((a) => a.id === id);
    if (idx === -1) throw new Error(`Assignment ${id} not found`);
    mutableAssignments = mutableAssignments.filter((a) => a.id !== id);
    return;
  }

  // Real fetch stub — uncomment and remove mock block above when FastAPI is ready
  // const res = await fetch(`/api/budgets/assignments/${id}`, { method: "DELETE" });
  // if (!res.ok) throw new Error("Failed to delete budget assignment");
  throw new Error("Real API not implemented");
}
