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

const PRIMARY_CATEGORIES = [
  'Food & Dining',
  'Transportation',
  'Housing',
  'Health & Medical',
  'Entertainment',
  'Shopping',
  'Utilities',
  'Income',
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
  it('has 65 transactions', () => {
    expect(mockTransactions).toHaveLength(65)
  })

  // Item 4: all 8 primary categories represented
  it('contains all 8 primary categories', () => {
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
