import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface DateRangeStore {
  month: number | null  // 1-12, or null for year view
  year: number
  setMonth: (month: number | null) => void
  setYear: (year: number) => void
  reset: () => void
}

export const useDateRangeStore = create<DateRangeStore>()(
  persist(
    (set) => ({
      month: new Date().getMonth() + 1,
      year: new Date().getFullYear(),
      setMonth: (month) => set({ month }),
      setYear: (year) => set({ year }),
      reset: () => {
        const now = new Date()
        set({ month: now.getMonth() + 1, year: now.getFullYear() })
      },
    }),
    {
      name: 'budgy-date-range',
    },
  ),
)
