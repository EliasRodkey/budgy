import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ArrowLeftRight,
  Tag,
  BarChart2,
  Wallet,
  ListFilter,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
} from 'lucide-react'
import { useSidebarStore } from '@/store/sidebar'
import { useMockMode } from '@/store/mockMode'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', Icon: ArrowLeftRight },
  { to: '/categories', label: 'Categories', Icon: Tag },
  { to: '/analytics', label: 'Analytics', Icon: BarChart2 },
  { to: '/budgets', label: 'Budgets', Icon: Wallet },
  { to: '/rules', label: 'Rules', Icon: ListFilter },
]

export default function Sidebar() {
  const { collapsed, toggleCollapsed } = useSidebarStore()
  const { isMockMode, toggleMockMode } = useMockMode()
  const queryClient = useQueryClient()

  function handleMockToggle() {
    toggleMockMode()
    queryClient.invalidateQueries()
  }

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-all duration-200',
        collapsed ? 'w-14' : 'w-56',
      )}
    >
      {/* Logo area */}
      <div className={cn('flex items-center h-14 px-3 border-b border-sidebar-border', collapsed ? 'justify-center' : 'justify-between')}>
        {!collapsed && (
          <span className="font-semibold text-sidebar-foreground tracking-tight">Budgy</span>
        )}
        <button
          onClick={toggleCollapsed}
          className="p-1.5 rounded-md hover:bg-sidebar-accent text-sidebar-foreground/60 hover:text-sidebar-foreground transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {navItems.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-2 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                collapsed && 'justify-center',
              )
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Demo Mode toggle */}
      <div className={cn('px-2 py-3 border-t border-sidebar-border', collapsed && 'flex justify-center')}>
        <button
          type="button"
          onClick={handleMockToggle}
          title={collapsed ? (isMockMode ? 'Demo Mode ON' : 'Demo Mode OFF') : undefined}
          className={cn(
            'flex items-center gap-2.5 w-full px-2 py-2 rounded-md text-sm transition-colors',
            isMockMode
              ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
              : 'text-sidebar-foreground/50 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
            collapsed && 'justify-center w-auto',
          )}
        >
          <FlaskConical size={16} className="shrink-0" />
          {!collapsed && (
            <span className="flex-1 text-left text-xs font-medium">Demo Mode</span>
          )}
          {!collapsed && (
            <span
              className={cn(
                'text-xs rounded-full px-1.5 py-0.5 font-medium',
                isMockMode
                  ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                  : 'bg-muted text-muted-foreground',
              )}
            >
              {isMockMode ? 'ON' : 'OFF'}
            </span>
          )}
        </button>
      </div>
    </aside>
  )
}
