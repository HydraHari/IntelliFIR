import React, { useState, useEffect } from 'react'
import {
  LogOut,
  Moon,
  Sun,
  ShieldCheck,
  Search,
  Sparkles,
  Command,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'

export const Header: React.FC = () => {
  const { user, logout } = useAuth()
  const isDemo = import.meta.env.VITE_DEMO_MODE === 'true'
  const [isDark, setIsDark] = useState<boolean>(() => {
    return document.documentElement.classList.contains('dark') ||
      localStorage.getItem('theme') === 'dark'
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  const toggleTheme = () => setIsDark(!isDark)

  return (
    <header className="h-14 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-30 transition-colors">
      {/* Left: Breadcrumbs / Active Context */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span className="font-medium text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            IntelliFIR Case Management
          </span>
          <span className="text-slate-300 dark:text-slate-700">/</span>
          <span className="text-slate-600 dark:text-slate-400 font-mono text-[11px]">
            v1.0.0-PROD
          </span>
        </div>

        {isDemo && (
          <Badge
            variant="outline"
            className="text-[10px] font-medium bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800/60 flex items-center gap-1 py-0.5 px-2"
          >
            <Sparkles className="h-2.5 w-2.5" /> Fictional Research Mode
          </Badge>
        )}
      </div>

      {/* Right: Quick Tools & Profile */}
      <div className="flex items-center gap-3">
        {/* Quick Search Shortcut Display */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-400 text-xs">
          <Search className="h-3.5 w-3.5" />
          <span className="text-[11px]">Search cases...</span>
          <kbd className="ml-2 px-1.5 py-0.5 text-[9px] font-mono bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded shadow-2xs text-slate-500">
            ⌘K
          </kbd>
        </div>

        {/* Theme Toggle Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={toggleTheme}
          className="h-8 w-8 p-0 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 rounded-md"
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
        </Button>

        <div className="h-4 w-[1px] bg-slate-200 dark:bg-slate-800" />

        {/* User Card */}
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-full bg-navy-800 dark:bg-slate-800 border border-navy-700 dark:border-slate-700 flex items-center justify-center text-white text-xs font-semibold shadow-2xs">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="text-left hidden lg:block">
            <p className="text-xs font-medium text-slate-800 dark:text-slate-200 leading-tight">
              {user?.full_name}
            </p>
            <p className="text-[10px] text-slate-400 capitalize font-mono">
              {user?.role}
            </p>
          </div>
        </div>

        {/* Logout */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => logout()}
          className="h-8 px-2.5 gap-1.5 text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:border-rose-200 dark:hover:border-rose-900/50 text-xs rounded-md"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Sign Out</span>
        </Button>
      </div>
    </header>
  )
}
