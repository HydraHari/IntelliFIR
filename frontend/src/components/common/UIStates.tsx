import React from 'react'
import { AlertCircle, RefreshCw, FolderSearch, Loader2 } from 'lucide-react'
import { Button } from '../ui/button'

export const LoadingSpinner: React.FC<{ label?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  label = 'Loading case records...',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-8 w-8' : 'h-6 w-6'

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 gap-3 text-center">
      <Loader2 className={`${sizeClass} animate-spin text-blue-600 dark:text-blue-400`} />
      <span className="text-xs font-medium text-slate-500 dark:text-slate-400 tracking-wide">
        {label}
      </span>
    </div>
  )
}

export const SkeletonRow: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-3 py-2">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="h-10 rounded-md bg-slate-200/60 dark:bg-slate-800/60 animate-pulse"
      />
    ))}
  </div>
)

export const EmptyState: React.FC<{
  title: string
  description: string
  action?: React.ReactNode
  icon?: React.ReactNode
}> = ({
  title,
  description,
  action,
  icon = <FolderSearch className="h-6 w-6 text-slate-400" />,
}) => (
  <div className="flex flex-col items-center justify-center py-16 px-6 text-center border border-dashed border-slate-200 dark:border-slate-800/80 rounded-xl bg-white/50 dark:bg-slate-900/30 backdrop-blur-2xs">
    <div className="h-12 w-12 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3 text-slate-400 shadow-2xs">
      {icon}
    </div>
    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-1">
      {title}
    </h3>
    <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mb-4 leading-relaxed">
      {description}
    </p>
    {action}
  </div>
)

export const ErrorState: React.FC<{
  title?: string
  message: string
  onRetry?: () => void
}> = ({
  title = 'System Error Encountered',
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center p-8 text-center border border-rose-200 dark:border-rose-900/50 rounded-xl bg-rose-50/50 dark:bg-rose-950/20">
    <div className="h-10 w-10 rounded-full bg-rose-100 dark:bg-rose-900/40 flex items-center justify-center mb-3 text-rose-600 dark:text-rose-400">
      <AlertCircle className="h-5 w-5" />
    </div>
    <h4 className="text-sm font-semibold text-rose-900 dark:text-rose-200 mb-1">
      {title}
    </h4>
    <p className="text-xs text-rose-700 dark:text-rose-400 max-w-md mb-4 leading-relaxed font-mono">
      {message}
    </p>
    {onRetry && (
      <Button
        variant="outline"
        size="sm"
        onClick={onRetry}
        className="gap-2 text-xs border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-300 hover:bg-rose-100/50"
      >
        <RefreshCw className="h-3.5 w-3.5" />
        Retry Operation
      </Button>
    )}
  </div>
)
