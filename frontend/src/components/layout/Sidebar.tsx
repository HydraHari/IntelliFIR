import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FilePlus2,
  FolderKanban,
  SearchCode,
  Scale,
  Sparkles,
  Cpu,
  BarChart3,
  Shield,
  Activity,
  CheckCircle2,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Badge } from '../ui/badge'

interface NavGroup {
  label: string
  items: {
    name: string
    to: string
    icon: React.ComponentType<{ className?: string }>
    badge?: string
  }[]
}

const navGroups: NavGroup[] = [
  {
    label: 'Core Workflow',
    items: [
      { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
      { name: 'New Ingestion', to: '/complaints/upload', icon: FilePlus2 },
      { name: 'Case Registry', to: '/cases', icon: FolderKanban },
    ],
  },
  {
    label: 'Decision Support',
    items: [
      { name: 'Similar Cases', to: '/similar-cases', icon: SearchCode },
      { name: 'Legal Reference', to: '/legal', icon: Scale },
      { name: 'RAG Assistant', to: '/assistant', icon: Sparkles, badge: 'AI' },
    ],
  },
  {
    label: 'Governance & Metrics',
    items: [
      { name: 'Model Engine', to: '/models', icon: Cpu },
      { name: 'Research Benchmark', to: '/evaluation', icon: BarChart3 },
    ],
  },
]

export const Sidebar: React.FC = () => {
  const { user } = useAuth()

  return (
    <aside className="w-64 flex-shrink-0 bg-[#0B132B] text-slate-300 flex flex-col border-r border-slate-800/80 select-none">
      {/* Brand Header */}
      <div className="h-14 flex items-center px-5 border-b border-slate-800/80 gap-3">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-sm ring-1 ring-white/20">
          <Shield className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-white tracking-tight text-sm">
              IntelliFIR
            </span>
            <span className="text-[9px] font-mono px-1 py-0.2 bg-blue-500/20 text-blue-300 rounded border border-blue-400/30">
              PRO
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-medium tracking-wide block truncate">
            Evidence-Grounded Legal AI
          </span>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1">
            <p className="px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 text-xs font-medium rounded-md transition-all group ${
                        isActive
                          ? 'bg-blue-600/15 text-white font-semibold border-l-2 border-blue-500 pl-[10px]'
                          : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="h-4 w-4 flex-shrink-0 text-slate-400 group-hover:text-slate-200 transition-colors" />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Audit & Legal Guardrail Callout */}
      <div className="mx-3 mb-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 space-y-1.5">
        <div className="flex items-center justify-between text-slate-300 font-medium">
          <span className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-semibold tracking-wider uppercase">
            <CheckCircle2 className="h-3 w-3" /> Human-In-The-Loop
          </span>
        </div>
        <p className="text-[10px] text-slate-400 leading-relaxed">
          All generated FIR drafts require authorized officer sign-off before official registration.
        </p>
      </div>

      {/* Role Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-[#070D1E] flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs text-white font-medium">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-200 truncate">
              {user?.full_name || 'Authorized Officer'}
            </p>
            <p className="text-[10px] text-slate-400 truncate font-mono">
              {user?.email}
            </p>
          </div>
        </div>
        <Badge
          variant="outline"
          className="text-[9px] uppercase tracking-wider font-mono border-slate-700 text-slate-300 bg-slate-800/50"
        >
          {user?.role}
        </Badge>
      </div>
    </aside>
  )
}
