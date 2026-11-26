import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText,
  FileCheck2,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Upload,
  PlusCircle,
  Search,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
  Cpu,
  Layers,
  ChevronRight,
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { dashboardApi, type DashboardStats } from '../api/dashboard'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { LoadingSpinner, EmptyState } from '../components/common/UIStates'

const STATUS_PALETTE: Record<string, { label: string; color: string }> = {
  uploaded: { label: 'Uploaded', color: '#94a3b8' },
  processing: { label: 'Processing', color: '#3b82f6' },
  draft_generated: { label: 'Draft Generated', color: '#6366f1' },
  validation_required: { label: 'Needs Validation', color: '#f59e0b' },
  under_review: { label: 'Under Review', color: '#f97316' },
  reviewed: { label: 'Approved', color: '#10b981' },
  archived: { label: 'Archived', color: '#64748b' },
}

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await dashboardApi.getStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load dashboard stats:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Compiling real-time case analytics..." />
  }

  const isEmpty = !stats || stats.total_complaints === 0

  const reviewedCount =
    stats?.complaints_by_status.find((s) => s.status === 'reviewed')?.count || 0

  return (
    <div className="space-y-6">
      {/* Page Header with Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Operational Command Center
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              Live Stream
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Real-time pipeline monitoring of citizen complaints, evidence extraction, and human validation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link to="/complaints/upload">
            <Button
              variant="primary"
              size="sm"
              className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white shadow-2xs font-medium"
            >
              <Upload className="h-3.5 w-3.5" />
              <span>Ingest Document</span>
            </Button>
          </Link>
          <Link to="/complaints/upload?tab=manual">
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium"
            >
              <PlusCircle className="h-3.5 w-3.5" />
              <span>Manual Complaint</span>
            </Button>
          </Link>
        </div>
      </div>

      {isEmpty ? (
        <EmptyState
          title="Case registry is currently empty"
          description="Upload an official complaint (PDF, DOCX, scanned image, or text) to initiate automated entity extraction and draft synthesis."
          action={
            <Link to="/complaints/upload">
              <Button size="sm" className="gap-2 text-xs bg-blue-600 text-white">
                <Upload className="h-4 w-4" />
                <span>Upload First Complaint</span>
              </Button>
            </Link>
          }
        />
      ) : (
        <>
          {/* Top KPI Cards (5 metrics) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
            {/* 1. Total Complaints */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                <span className="text-[11px] font-semibold tracking-wider uppercase">
                  Total Complaints
                </span>
                <div className="h-7 w-7 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300">
                  <FileText className="h-4 w-4" />
                </div>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {stats.total_complaints}
                </span>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                  Active Intake
                </span>
              </div>
            </div>

            {/* 2. Drafts Generated */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                <span className="text-[11px] font-semibold tracking-wider uppercase">
                  Drafts Generated
                </span>
                <div className="h-7 w-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                  <FileCheck2 className="h-4 w-4" />
                </div>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold tracking-tight text-indigo-950 dark:text-indigo-200">
                  {stats.total_drafts}
                </span>
                <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium">
                  AI Synthesized
                </span>
              </div>
            </div>

            {/* 3. Awaiting Review */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                <span className="text-[11px] font-semibold tracking-wider uppercase">
                  Awaiting Review
                </span>
                <div className="h-7 w-7 rounded-lg bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
                  <Clock className="h-4 w-4" />
                </div>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold tracking-tight text-amber-900 dark:text-amber-200">
                  {stats.pending_reviews}
                </span>
                <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">
                  Queue Priority
                </span>
              </div>
            </div>

            {/* 4. Reviewed FIRs */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                <span className="text-[11px] font-semibold tracking-wider uppercase">
                  Approved FIRs
                </span>
                <div className="h-7 w-7 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-4 w-4" />
                </div>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold tracking-tight text-emerald-900 dark:text-emerald-200">
                  {reviewedCount}
                </span>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                  Official Sign-off
                </span>
              </div>
            </div>

            {/* 5. Validation Warnings */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                <span className="text-[11px] font-semibold tracking-wider uppercase">
                  Validation Flags
                </span>
                <div className="h-7 w-7 rounded-lg bg-rose-50 dark:bg-rose-950/50 flex items-center justify-center text-rose-600 dark:text-rose-400">
                  <AlertTriangle className="h-4 w-4" />
                </div>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold tracking-tight text-rose-900 dark:text-rose-200">
                  {stats.total_findings}
                </span>
                <span className="text-[10px] text-rose-600 dark:text-rose-400 font-medium">
                  Audited Issues
                </span>
              </div>
            </div>
          </div>

          {/* Pipeline Analytics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Status Breakdown Donut Chart */}
            <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
              <CardHeader className="pb-2 pt-4 px-5 border-b border-slate-100 dark:border-slate-800/80">
                <CardTitle className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center justify-between">
                  <span>Case Status Allocation</span>
                  <Layers className="h-3.5 w-3.5 text-slate-400" />
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Distribution of complaints across drafting lifecycle
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                <div className="h-52 w-full flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stats.complaints_by_status}
                        dataKey="count"
                        nameKey="status"
                        cx="50%"
                        cy="50%"
                        innerRadius={46}
                        outerRadius={74}
                        paddingAngle={3}
                        stroke="none"
                      >
                        {stats.complaints_by_status.map((entry) => (
                          <Cell
                            key={`cell-${entry.status}`}
                            fill={STATUS_PALETTE[entry.status]?.color || '#94a3b8'}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0F172A',
                          border: 'none',
                          borderRadius: '8px',
                          color: '#F8FAFC',
                          fontSize: '11px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px]">
                  {stats.complaints_by_status.map((item) => (
                    <div key={item.status} className="flex items-center gap-1.5 truncate">
                      <span
                        className="h-2 w-2 rounded-full flex-shrink-0"
                        style={{
                          backgroundColor: STATUS_PALETTE[item.status]?.color || '#94a3b8',
                        }}
                      />
                      <span className="text-slate-600 dark:text-slate-400 truncate">
                        {STATUS_PALETTE[item.status]?.label || item.status}:
                      </span>
                      <span className="font-semibold text-slate-900 dark:text-slate-200">
                        {item.count}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Workflow Pipeline Volume Bar Chart */}
            <Card className="lg:col-span-2 border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
              <CardHeader className="pb-2 pt-4 px-5 border-b border-slate-100 dark:border-slate-800/80">
                <CardTitle className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center justify-between">
                  <span>Intake & Processing Throughput</span>
                  <TrendingUp className="h-3.5 w-3.5 text-slate-400" />
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Volume of active complaints across consecutive workflow gates
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={stats.complaints_by_status.map((item) => ({
                        statusName: STATUS_PALETTE[item.status]?.label || item.status,
                        count: item.count,
                      }))}
                      margin={{ top: 10, right: 10, left: -25, bottom: 25 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.15} />
                      <XAxis
                        dataKey="statusName"
                        tick={{ fontSize: 10, fill: '#64748b' }}
                        interval={0}
                        angle={-15}
                        textAnchor="end"
                      />
                      <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#64748b' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0F172A',
                          border: 'none',
                          borderRadius: '8px',
                          color: '#F8FAFC',
                          fontSize: '11px',
                        }}
                      />
                      <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Audit Log Activity & Quick Navigation */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Audit Trail Feed */}
            <Card className="lg:col-span-2 border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
              <CardHeader className="pb-2 pt-4 px-5 border-b border-slate-100 dark:border-slate-800/80">
                <CardTitle className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center justify-between">
                  <span>Audited System Events</span>
                  <span className="text-[10px] font-mono font-normal text-slate-400">
                    Immutable SHA-256 Ledger
                  </span>
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Chronological record of extraction, draft updates, and reviewer sign-offs
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {stats.recent_activity.length === 0 ? (
                    <p className="p-6 text-xs text-slate-400 text-center">
                      No system events recorded.
                    </p>
                  ) : (
                    stats.recent_activity.slice(0, 6).map((log) => (
                      <div
                        key={log.id}
                        className="px-5 py-3 flex items-center justify-between text-xs hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="font-semibold text-slate-800 dark:text-slate-200 capitalize truncate">
                              {log.action.replace(/_/g, ' ')}
                            </p>
                            <p className="text-[10px] text-slate-400 font-mono truncate">
                              {log.resource_type} • ID:{' '}
                              {log.resource_id ? log.resource_id.slice(0, 12) : 'N/A'}
                            </p>
                          </div>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono flex-shrink-0 ml-4">
                          {new Date(log.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Investigation Modules */}
            <Card className="lg:col-span-1 border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
              <CardHeader className="pb-2 pt-4 px-5 border-b border-slate-100 dark:border-slate-800/80">
                <CardTitle className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                  Direct Tools
                </CardTitle>
                <CardDescription className="text-[11px] text-slate-500">
                  Fast-access AI capabilities
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 space-y-2.5">
                <Link to="/similar-cases" className="block group">
                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-blue-500/50 hover:bg-blue-50/30 dark:hover:bg-blue-950/20 transition-all flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="h-8 w-8 rounded-md bg-blue-50 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
                        <Search className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          Semantic Case Search
                        </p>
                        <p className="text-[10px] text-slate-400">
                          Dense vector retrieval on historical FIRs
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </Link>

                <Link to="/legal" className="block group">
                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 hover:bg-emerald-50/30 dark:hover:bg-emerald-950/20 transition-all flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="h-8 w-8 rounded-md bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                          Penal Code Retrieval
                        </p>
                        <p className="text-[10px] text-slate-400">
                          BNS & IT Act statutory grounding
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </Link>

                <Link to="/assistant" className="block group">
                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-50/30 dark:hover:bg-indigo-950/20 transition-all flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="h-8 w-8 rounded-md bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                        <Sparkles className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                          Investigative RAG Chat
                        </p>
                        <p className="text-[10px] text-slate-400">
                          Cross-case queries with source citations
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </Link>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
