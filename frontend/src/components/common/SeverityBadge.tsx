import React from 'react'

interface SeverityBadgeProps {
  severity: string
  className?: string
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, className = '' }) => {
  const norm = severity.toLowerCase()

  if (norm === 'high' || norm === 'critical') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60 ${className}`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-rose-600 animate-pulse" />
        High Severity
      </span>
    )
  }

  if (norm === 'medium') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 ${className}`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
        Medium
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 ${className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      Low
    </span>
  )
}
