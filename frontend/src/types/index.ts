// API envelope
export interface ApiResponse<T> {
  data: T;
  meta?: {
    total: number;
    page: number;
    page_size: number;
  };
}

// Core domain types

export interface Transaction {
  id: string;
  authorizedDate: string; // ISO 8601
  postedDate: string; // ISO 8601
  status: string
  accountName: string;
  description: string;
  primaryCategory: string;
  detailedCategory: string;
  amount: number; // float, dollars (negative = expense)
  repayment: boolean;
  exclude: boolean;
  notes?: string;    // max 300 chars, edit modal only
  tags?: string[];   // max 10 tags, each max 30 chars, no spaces
}

export interface Category {
  id: string;
  name: string;
  level: "primary" | "detailed";
  parentId: string | null; // null for primary categories
}

export interface CategorySpend {
  categoryId: string;
  categoryName: string;
  amount: number;
  transactionCount: number;
  avgPerTransaction: number;
  monthlyLimit: number | null;
  percentOfLimit: number | null;
  isOverBudget: boolean;
}

export interface MonthlySummary {
  month: string; // YYYY-MM
  totalIncome: number;
  totalExpenses: number;
  net: number;
  byCategory: CategorySpend[];
}

export interface AnalyticsSeries {
  labels: string[]; // YYYY-MM month labels
  datasets: {
    categoryId: string;
    categoryName: string;
    values: number[];
  }[];
}

export interface Budget {
  id: string;
  dateCreated: string; // ISO 8601
  categoryLimits: Record<string, number>; // primaryCategory name → monthly limit
  monthlyIncomeEstimate: number; // user-entered expected monthly income
  netGainOrLoss: number; // derived: monthlyIncomeEstimate - sum(categoryLimits)
  note: string | null; // optional user note
}

export interface BudgetAssignment {
  id: string;
  budgetId: string;
  effectiveFrom: string; // YYYY-MM
  note: string | null;
}

export interface AISummary {
  generatedAt: string; // ISO 8601
  recap: string;
  anomalies: string[];
  suggestions: string[];
}
