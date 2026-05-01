import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppShell from '@/components/layout/AppShell'
import Dashboard from '@/pages/Dashboard'
import Transactions from '@/pages/Transactions'
import Categories from '@/pages/Categories'
import CategoryDetail from '@/pages/CategoryDetail'
import SubcategoryDetail from '@/pages/SubcategoryDetail'
import Analytics from '@/pages/Analytics'
import Budgets from '@/pages/Budgets'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="categories" element={<Categories />} />
          <Route path="categories/:primaryCategory" element={<CategoryDetail />} />
          <Route path="categories/:primaryCategory/:detailedCategory" element={<SubcategoryDetail />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="budgets" element={<Budgets />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
