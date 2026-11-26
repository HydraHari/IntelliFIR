import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Search,
  Filter,
  Plus,
  ArrowRight,
  Eye,
  FileText,
  FileCheck2,
  ShieldAlert,
  Calendar,
  Layers,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  X,
} from 'lucide-react'
import { complaintsApi } from '../api/complaints'
import type { ComplaintListItem } from '../types/complaint'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { StatusBadge } from '../components/common/StatusBadge'
import { LoadingSpinner, EmptyState, SkeletonRow } from '../components/common/UIStates'

export const CaseListPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [total, setTotal] = useState(0)
  const [sortField, setSortField] = useState<'date' | 'ref' | 'title'>('date')
  const [sortAsc, setSortAsc] = useState(false)

  useEffect(() => {
    loadComplaints()
  }, [statusFilter])

  const loadComplaints = async () => {
    setLoading(true)
    try {
      const resp = await complaintsApi.list({
        search: search || undefined,
        status: statusFilter || undefined,
      })
      setComplaints(resp.items || [])
      setTotal(resp.total || 0)
    } catch (err) {
      console.error('Failed to load complaints:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loadComplaints()
  }

  const sortedComplaints = [...complaints].sort((a, b) => {
    if (sortField === 'ref') {
      return sortAsc
        ? a.reference_id.localeCompare(b.reference_id)
        : b.reference_id.localeCompare(a.reference_id)
    }
    if (sortField === 'title') {
      return sortAsc ? a.title.localeCompare(b.title) : b.title.localeCompare(a.title)
    }
    const d1 = new Date(a.created_at).getTime()
    const d2 = new Date(b.created_at).getTime()
    return sortAsc ? d1 - d2 : d2 - d1
  })

  const toggleSort = (field: 'date' | 'ref' | 'title') => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Case Registry & FIR Docket
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold border border-slate-200 dark:border-slate-700">
              {total} Total Cases
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Comprehensive audit record of citizen complaints, extracted facts, and generated draft statuses.
          </p>
        </div>

        <Link to="/complaints/upload">
          <Button
            variant="primary"
            size="sm"
            className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white shadow-2xs font-medium"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Ingest New Complaint</span>
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
        <CardContent className="p-3.5">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row items-center gap-2.5">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <Input
                placeholder="Search reference ID, complainant statement, incident landmark..."
                className="pl-9 h-8 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              {search && (
                <button
                  type="button"
                  onClick={() => {
                    setSearch('')
                    loadComplaints()
                  }}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                className="h-8 px-2.5 rounded-md border border-slate-200 dark:border-slate-800 text-xs bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 focus:outline-none"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="uploaded">Uploaded</option>
                <option value="processing">Processing</option>
                <option value="draft_generated">Draft Generated</option>
                <option value="validation_required">Validation Required</option>
                <option value="under_review">Under Review</option>
                <option value="reviewed">Approved</option>
                <option value="archived">Archived</option>
              </select>

              <Button
                type="submit"
                variant="secondary"
                size="sm"
                className="h-8 px-3 text-xs bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300"
              >
                Filter
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Case Table */}
      <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90 overflow-hidden">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6">
              <LoadingSpinner label="Querying case registry..." />
            </div>
          ) : sortedComplaints.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No complaint dockets matched your criteria"
                description="Try refining your query, clearing the status filter, or ingesting a new complaint document."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-slate-50/80 dark:bg-slate-950/60 border-b border-slate-200/80 dark:border-slate-800">
                  <TableRow className="hover:bg-transparent">
                    <TableHead
                      className="w-36 text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer select-none"
                      onClick={() => toggleSort('ref')}
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Reference ID</span>
                        <ArrowUpDown className="h-3 w-3 text-slate-400" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer select-none"
                      onClick={() => toggleSort('title')}
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Incident Title & Scope</span>
                        <ArrowUpDown className="h-3 w-3 text-slate-400" />
                      </div>
                    </TableHead>
                    <TableHead className="w-32 text-xs font-bold text-slate-700 dark:text-slate-300">
                      Incident Date
                    </TableHead>
                    <TableHead className="w-36 text-xs font-bold text-slate-700 dark:text-slate-300">
                      Lifecycle State
                    </TableHead>
                    <TableHead
                      className="w-28 text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer select-none"
                      onClick={() => toggleSort('date')}
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Created</span>
                        <ArrowUpDown className="h-3 w-3 text-slate-400" />
                      </div>
                    </TableHead>
                    <TableHead className="w-56 text-right text-xs font-bold text-slate-700 dark:text-slate-300">
                      Pipeline Actions
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {sortedComplaints.map((c) => (
                    <TableRow
                      key={c.id}
                      className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <TableCell className="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400 py-3">
                        <Link to={`/cases/${c.id}`} className="hover:underline">
                          {c.reference_id}
                        </Link>
                      </TableCell>
                      <TableCell className="text-xs font-medium text-slate-900 dark:text-slate-100 max-w-sm">
                        <div className="truncate font-semibold">{c.title}</div>
                        <div className="text-[11px] text-slate-400 truncate mt-0.5">
                          {c.incident_location || 'Jurisdiction Pending'}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-slate-500 dark:text-slate-400">
                        {c.incident_date || '—'}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={c.status} />
                      </TableCell>
                      <TableCell className="text-[11px] text-slate-400 font-mono">
                        {new Date(c.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right py-2">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link to={`/cases/${c.id}`}>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2 text-[11px] gap-1 text-slate-600 dark:text-slate-300"
                              title="Case Docket Details"
                            >
                              <Eye className="h-3 w-3" />
                              <span>View</span>
                            </Button>
                          </Link>

                          <Link to={`/cases/${c.id}/evidence`}>
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 px-2 text-[11px] gap-1 border-slate-200 dark:border-slate-800 text-blue-600 dark:text-blue-400 hover:bg-blue-50/50"
                              title="Interactive Evidence Provenance"
                            >
                              <FileText className="h-3 w-3" />
                              <span>Evidence</span>
                            </Button>
                          </Link>

                          <Link to={`/cases/${c.id}/draft`}>
                            <Button
                              variant="primary"
                              size="sm"
                              className="h-7 px-2.5 text-[11px] gap-1 bg-blue-600 hover:bg-blue-700 text-white"
                              title="First Information Report Draft"
                            >
                              <span>FIR Draft</span>
                            </Button>
                          </Link>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Table Footer / Counter */}
          <div className="px-5 py-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {sortedComplaints.length} of {total} registered cases
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                className="h-6 px-2 text-[10px] border-slate-200 dark:border-slate-800"
                disabled
              >
                <ChevronLeft className="h-3 w-3" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-6 px-2 text-[10px] border-slate-200 dark:border-slate-800"
                disabled
              >
                <ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
