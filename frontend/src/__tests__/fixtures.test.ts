import { describe, it, expect } from 'vitest'
import {
  mockTransactions,
  mockCategories,
  mockBudgets,
  mockBudgetAssignments,
  mockMonthlySummaries,
  mockAnalyticsSeries,
  mockAISummary,
} from './fixtures/index'

// All 16 primary categories from PrimaryCategories enum in analysis_utils.py
const PRIMARY_CATEGORIES = [
  'Income',
  'Transfers',
  'Debt payments',
  'Investments',
  'Bank fees',
  'Food & drink',
  'Shopping',
  'Housing & utilities',
  'Health & wellness',
  'Entertainment',
  'Insurance',
  'Services',
  'Transportation',
  'Travel',
  'Government & charity',
  'Other',
] as const

describe('fixture exports', () => {
  it('all named exports are defined', () => {
    expect(mockCategories).toBeDefined()
    expect(mockTransactions).toBeDefined()
    expect(mockBudgets).toBeDefined()
    expect(mockBudgetAssignments).toBeDefined()
    expect(mockMonthlySummaries).toBeDefined()
    expect(mockAnalyticsSeries).toBeDefined()
    expect(mockAISummary).toBeDefined()
  })
})

describe('mockTransactions', () => {
  it('has 74 transactions', () => {
    expect(mockTransactions).toHaveLength(74)
  })

  // Item 4: all 16 primary categories represented
  it('contains all 16 primary categories', () => {
    const found = new Set(mockTransactions.map((tx) => tx.primaryCategory))
    for (const cat of PRIMARY_CATEGORIES) {
      expect(found.has(cat), `missing category: ${cat}`).toBe(true)
    }
  })

  // Item 5: flagged and uncategorized transactions present
  it('contains flagged transactions', () => {
    expect(mockTransactions.filter((tx) => tx.isFlagged).length).toBeGreaterThan(0)
  })

  it('contains uncategorized flagged transactions with empty category strings', () => {
    const uncategorized = mockTransactions.filter(
      (tx) => tx.isFlagged && tx.primaryCategory === '' && tx.detailedCategory === ''
    )
    expect(uncategorized.length).toBeGreaterThan(0)
  })
})
