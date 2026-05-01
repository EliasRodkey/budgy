import type { Budget, BudgetAssignment } from "../types";
import { mockBudgets, mockBudgetAssignments } from "../__tests__/fixtures";
import { useMockMode } from "../store/mockMode";

const isMock = () => useMockMode.getState().isMockMode;

// ─── Budgets ──────────────────────────────────────────────────────────────────

export async function getBudgets(): Promise<Budget[]> {
  if (isMock()) return [...mockBudgets];
  const res = await fetch("/api/budgets");
  if (!res.ok) throw new Error("Failed to fetch budgets");
  const json = await res.json();
  return json.data as Budget[];
}

export async function createBudget(
  payload: Omit<Budget, "id" | "dateCreated">,
): Promise<Budget> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch("/api/budgets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create budget");
  const json = await res.json();
  return json as Budget;
}

export async function updateBudget(
  id: number,
  payload: Partial<Omit<Budget, "id" | "dateCreated">>,
): Promise<Budget> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch(`/api/budgets/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update budget");
  const json = await res.json();
  return json as Budget;
}

export async function deleteBudget(id: number): Promise<void> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch(`/api/budgets/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete budget");
}

// ─── Budget Assignments ───────────────────────────────────────────────────────

export async function getBudgetAssignments(): Promise<BudgetAssignment[]> {
  if (isMock()) return [...mockBudgetAssignments];
  const res = await fetch("/api/budgets/assignments");
  if (!res.ok) throw new Error("Failed to fetch budget assignments");
  const json = await res.json();
  return json.data as BudgetAssignment[];
}

export async function createBudgetAssignment(
  payload: Omit<BudgetAssignment, "id">,
): Promise<BudgetAssignment> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch("/api/budgets/assignments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create budget assignment");
  const json = await res.json();
  return json as BudgetAssignment;
}

export async function deleteBudgetAssignment(id: number): Promise<void> {
  if (isMock()) throw new Error("Mock disabled");
  const res = await fetch(`/api/budgets/assignments/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete budget assignment");
}
