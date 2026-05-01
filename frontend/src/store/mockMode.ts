import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface MockModeStore {
  isMockMode: boolean
  toggleMockMode: () => void
  setMockMode: (value: boolean) => void
}

export const useMockMode = create<MockModeStore>()(
  persist(
    (set) => ({
      isMockMode: false,
      toggleMockMode: () => set((state) => ({ isMockMode: !state.isMockMode })),
      setMockMode: (value) => set({ isMockMode: value }),
    }),
    {
      name: 'budgy-mock-mode',
    },
  ),
)
