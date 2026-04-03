import { Sun, Moon } from 'lucide-react'
import { useThemeStore } from '@/store/theme'

export default function Header() {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <header className="h-14 flex items-center justify-end px-6 border-b border-border bg-background">
      <button
        onClick={toggleTheme}
        className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors text-muted-foreground"
        aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
      >
        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
      </button>
    </header>
  )
}
