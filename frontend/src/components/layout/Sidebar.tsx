import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ArrowLeftRight,
  Tag,
  BarChart2,
  Wallet,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useSidebarStore } from '@/store/sidebar'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', Icon: ArrowLeftRight },
  { to: '/categories', label: 'Categories', Icon: Tag },
  { to: '/analytics', label: 'Analytics', Icon: BarChart2 },
  { to: '/budgets', label: 'Budgets', Icon: Wallet },
]

export default function Sidebar() {
  const { collapsed, toggleCollapsed } = useSidebarStore()

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
    </aside>
  )
}
