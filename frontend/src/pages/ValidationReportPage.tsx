import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Clock,
  Layers,
  ChevronRight,
  ShieldCheck,
  RotateCw,
  Send,
  MessageSquare,
  ShieldAlert,
  ArrowRight,
  Filter,
  Check,
  X,
  FileText,
} from 'lucide-react'
import { validationApi } from '../api/validation'
import { draftsApi } from '../api/drafts'
import { complaintsApi } from '../api/complaints'
import type { Complaint } from '../types/complaint'
import type { FIRDraft } from '../types/draft'
import type { ValidationFinding } from '../types/validation'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { SeverityBadge } from '../components/common/SeverityBadge'
import { LoadingSpinner, EmptyState } from '../components/common/UIStates'

export const ValidationReportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [complaint, setComplaint] = useState<Complaint | null>(null)
  const [draft, setDraft] = useState<FIRDraft | null>(null)
  const [findings, setFindings] = useState<ValidationFinding[]>([])
  const [loading, setLoading] = useState(true)
  const [isValidating, setIsValidating] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [notesState, setNotesState] = useState<Record<string, string>>({})

  useEffect(() => {
    if (id) {
      loadValidationData(id)
    }
  }, [id])

  const loadValidationData = async (caseId: string) => {
    setLoading(true)
    try {
      const comp = await complaintsApi.get(caseId)
      setComplaint(comp)

      const draftData = await draftsApi.getForComplaint(caseId)
      setDraft(draftData)

      const rep = await validationApi.getForDraft(draftData.id)
      setFindings((rep as any).findings || [])
    } catch (err) {
      console.error('Failed to load validation report:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRunValidation = async () => {
    if (!draft) return
    setIsValidating(true)
    try {
      const rep = await validationApi.trigger(draft.id)
      setFindings((rep as any).findings || [])
    } catch (err) {
      console.error('Validation execution failed:', err)
    } finally {
      setIsValidating(false)
    }
  }

  const handleDecision = async (
    findingId: string,
    decision: 'accepted' | 'rejected' | 'needs_clarification'
  ) => {
    const notes = notesState[findingId] || ''
    try {
      await validationApi.updateFinding(findingId, {
        reviewer_action: decision,
        reviewer_notes: notes,
      })
      setFindings((prev) =>
        prev.map((f) =>
          f.id === findingId
            ? { ...f, reviewer_action: decision, reviewer_notes: notes }
            : f
        )
      )
    } catch (err) {
      console.error('Failed to record reviewer decision:', err)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Auditing draft consistency against source evidence..." />
  }

  if (!draft) {
    return (
      <EmptyState
        title="No FIR draft exists for validation"
        description="A preliminary draft must be generated before the independent factual consistency auditor can evaluate claims."
        action={
          <Link to={`/cases/${id}/draft`}>
            <Button size="sm" className="bg-blue-600 text-white text-xs">
              Go to Draft Generator
            </Button>
          </Link>
        }
      />
    )
  }

  const filteredFindings = findings.filter((f) => {
    if (activeCategory === 'all') return true
    return f.category === activeCategory
  })

  const highCount = findings.filter((f) => f.severity === 'high').length
  const medCount = findings.filter((f) => f.severity === 'medium').length
  const lowCount = findings.filter((f) => f.severity === 'low').length

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Breadcrumb and Run Action */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Link to="/cases" className="hover:text-slate-800 dark:hover:text-slate-200">
            Cases
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-400" />
          <Link
            to={`/cases/${id}`}
            className="hover:text-slate-800 dark:hover:text-slate-200 font-mono"
          >
            {complaint?.reference_id}
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-400" />
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            Independent Factual Validation Report
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleRunValidation}
          disabled={isValidating}
          className="h-8 gap-1.5 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          <RotateCw className={`h-3 w-3 ${isValidating ? 'animate-spin' : ''}`} />
          <span>{isValidating ? 'Auditing...' : 'Re-run Validator'}</span>
        </Button>
      </div>

      {/* Header and Severity Breakdown Banner */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5 shadow-2xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-amber-400" />
            <h1 className="text-sm font-bold tracking-tight uppercase tracking-wider text-white">
              Independent Consistency Validator
            </h1>
          </div>
          <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
            Directly cross-checks the draft FIR text against the raw complaint narrative to detect ungrounded facts, timeline conflicts, and missing statutory particulars.
          </p>
        </div>

        {/* Severity Metrics Strip */}
        <div className="flex items-center gap-4 bg-slate-950/70 px-4 py-2.5 rounded-lg border border-slate-800 font-mono text-xs">
          <div className="text-center">
            <span className="text-[9px] uppercase font-bold text-rose-400 block tracking-wider">
              High Risk
            </span>
            <span className="text-base font-bold text-white">{highCount}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div className="text-center">
            <span className="text-[9px] uppercase font-bold text-amber-400 block tracking-wider">
              Medium
            </span>
            <span className="text-base font-bold text-white">{medCount}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div className="text-center">
            <span className="text-[9px] uppercase font-bold text-emerald-400 block tracking-wider">
              Low
            </span>
            <span className="text-base font-bold text-white">{lowCount}</span>
          </div>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {[
          { id: 'all', label: 'All Findings' },
          { id: 'missing_information', label: 'Missing Info' },
          { id: 'unsupported_claim', label: 'Unsupported Claims' },
          { id: 'ambiguity', label: 'Ambiguity' },
          { id: 'contradiction', label: 'Contradictions' },
          { id: 'uncertainty', label: 'Uncertain Allegations' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveCategory(tab.id)}
            className={`px-3 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-all border ${
              activeCategory === tab.id
                ? 'bg-blue-600 text-white border-blue-600 shadow-2xs font-semibold'
                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Findings List */}
      <div className="space-y-3.5">
        {filteredFindings.length === 0 ? (
          <Card className="p-10 text-center border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
            <div className="flex flex-col items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                Zero Inconsistencies Detected in this Category
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed">
                The preliminary FIR claims are verified against the original citizen complaint text.
              </p>
            </div>
          </Card>
        ) : (
          filteredFindings.map((finding) => (
            <Card
              key={finding.id}
              className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90 overflow-hidden"
            >
              <div className="px-5 py-2.5 bg-slate-50/70 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] font-bold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                    {finding.id}
                  </span>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                    {finding.category.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2.5">
                  <SeverityBadge severity={finding.severity} />
                  {finding.reviewer_action && finding.reviewer_action !== 'pending' && (
                    <span className="text-[10px] font-mono font-medium capitalize px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                      Action: {finding.reviewer_action.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
              </div>

              <CardContent className="p-5 space-y-3.5">
                {/* Claim vs Evidence Side-by-Side Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  <div className="p-3 bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-900/40 rounded-lg">
                    <p className="text-[10px] font-bold text-rose-800 dark:text-rose-300 uppercase tracking-wider mb-1">
                      Draft Claim / Flagged Statement
                    </p>
                    <p className="text-xs font-medium text-slate-800 dark:text-slate-200 leading-snug">
                      {finding.draft_claim}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg">
                    <p className="text-[10px] font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1">
                      Source Complaint Evidence
                    </p>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-snug">
                      {finding.source_evidence || (
                        <span className="italic text-slate-400">
                          [Omitted / Missing in Original Statement]
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Explanation and Suggested Action */}
                <div className="space-y-1 text-xs leading-relaxed">
                  <p className="text-slate-600 dark:text-slate-400">
                    <strong className="text-slate-900 dark:text-slate-100 font-semibold">
                      Auditor Explanation:{' '}
                    </strong>
                    {finding.explanation}
                  </p>
                  {finding.suggested_action && (
                    <p className="text-blue-900 dark:text-blue-300 font-medium pt-0.5">
                      <strong className="font-semibold">Recommended Officer Action: </strong>
                      {finding.suggested_action}
                    </p>
                  )}
                </div>

                {/* Reviewer Action Bar */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <Button
                      variant={finding.reviewer_action === 'accepted' ? 'primary' : 'outline'}
                      size="sm"
                      onClick={() => handleDecision(finding.id, 'accepted')}
                      className={`h-7 text-[11px] ${
                        finding.reviewer_action === 'accepted'
                          ? 'bg-blue-600 text-white'
                          : 'border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <Check className="h-3 w-3 mr-1" />
                      <span>Accept Finding</span>
                    </Button>

                    <Button
                      variant={finding.reviewer_action === 'rejected' ? 'primary' : 'outline'}
                      size="sm"
                      onClick={() => handleDecision(finding.id, 'rejected')}
                      className={`h-7 text-[11px] ${
                        finding.reviewer_action === 'rejected'
                          ? 'bg-slate-800 text-white'
                          : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      <X className="h-3 w-3 mr-1" />
                      <span>Dismiss Finding</span>
                    </Button>

                    <Button
                      variant={
                        finding.reviewer_action === 'needs_clarification' ? 'primary' : 'outline'
                      }
                      size="sm"
                      onClick={() => handleDecision(finding.id, 'needs_clarification')}
                      className={`h-7 text-[11px] ${
                        finding.reviewer_action === 'needs_clarification'
                          ? 'bg-amber-600 text-white'
                          : 'border-slate-200 dark:border-slate-800 text-amber-700 dark:text-amber-400'
                      }`}
                    >
                      <HelpCircle className="h-3 w-3 mr-1" />
                      <span>Request Clarification</span>
                    </Button>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <input
                      type="text"
                      placeholder="Add officer notes..."
                      className="h-7 px-2.5 text-xs border border-slate-200 dark:border-slate-800 rounded-md w-full sm:w-56 bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200 focus:outline-none"
                      value={notesState[finding.id] || finding.reviewer_notes || ''}
                      onChange={(e) =>
                        setNotesState({ ...notesState, [finding.id]: e.target.value })
                      }
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
