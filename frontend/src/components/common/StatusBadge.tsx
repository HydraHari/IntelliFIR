import React from 'react'

interface StatusBadgeProps {
  status: string
  className?: string
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const normalized = status.toLowerCase()

  const configMap: Record<string, { label: string; dot: string; bg: string; text: string; border: string }> = {
    uploaded: {
      label: 'Uploaded',
      dot: 'bg-slate-400',
      bg: 'bg-slate-100 dark:bg-slate-800/60',
      text: 'text-slate-700 dark:text-slate-300',
      border: 'border-slate-200 dark:border-slate-700',
    },
    processing: {
      label: 'Processing',
      dot: 'bg-blue-500 animate-ping',
      bg: 'bg-blue-50 dark:bg-blue-950/40',
      text: 'text-blue-700 dark:text-blue-300',
      border: 'border-blue-200 dark:border-blue-800/60',
    },
    draft_generated: {
      label: 'Draft Generated',
      dot: 'bg-indigo-500',
      bg: 'bg-indigo-50 dark:bg-indigo-950/40',
      text: 'text-indigo-700 dark:text-indigo-300',
      border: 'border-indigo-200 dark:border-indigo-800/60',
    },
    validation_required: {
      label: 'Needs Validation',
      dot: 'bg-amber-500',
      bg: 'bg-amber-50 dark:bg-amber-950/40',
      text: 'text-amber-800 dark:text-amber-300',
      border: 'border-amber-200 dark:border-amber-800/60',
    },
    under_review: {
      label: 'Under Review',
      dot: 'bg-orange-500',
      bg: 'bg-orange-50 dark:bg-orange-950/40',
      text: 'text-orange-800 dark:text-orange-300',
      border: 'border-orange-200 dark:border-orange-800/60',
    },
    reviewed: {
      label: 'Reviewed & Approved',
      dot: 'bg-emerald-500',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      text: 'text-emerald-800 dark:text-emerald-300',
      border: 'border-emerald-200 dark:border-emerald-800/60',
    },
    archived: {
      label: 'Archived',
      dot: 'bg-slate-400',
      bg: 'bg-slate-100 dark:bg-slate-800/60',
      text: 'text-slate-500 dark:text-slate-400',
      border: 'border-slate-200 dark:border-slate-700',
    },
  }

  const current = configMap[normalized] || {
    label: status.replace(/_/g, ' '),
    dot: 'bg-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800/60',
    text: 'text-slate-700 dark:text-slate-300',
    border: 'border-slate-200 dark:border-slate-700',
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${current.bg} ${current.text} ${current.border} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${current.dot}`} />
      <span className="capitalize">{current.label}</span>
    </span>
  )
}
