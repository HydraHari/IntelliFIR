import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  FileText,
  FileEdit,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  ChevronRight,
  Calendar,
  MapPin,
  RotateCw,
  Cpu,
  Layers,
  Sparkles,
  AlertTriangle,
  FileCheck2,
  Lock,
} from 'lucide-react'
import { complaintsApi } from '../api/complaints'
import { reviewsApi } from '../api/reviews'
import type { Complaint } from '../types/complaint'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { StatusBadge } from '../components/common/StatusBadge'
import { LoadingSpinner } from '../components/common/UIStates'

export const CaseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [complaint, setComplaint] = useState<Complaint | null>(null)
  const [loading, setLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [reviewAction, setReviewAction] = useState('approved')
  const [reviewNotes, setReviewNotes] = useState('')
  const [isSubmittingReview, setIsSubmittingReview] = useState(false)
  const [reviewSuccess, setReviewSuccess] = useState(false)

  useEffect(() => {
    if (id) {
      loadComplaint(id)
    }
  }, [id])

  const loadComplaint = async (caseId: string) => {
    setLoading(true)
    try {
      const data = await complaintsApi.get(caseId)
      setComplaint(data)
    } catch (err) {
      console.error('Failed to load complaint:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRunProcessing = async () => {
    if (!id) return
    setIsProcessing(true)
    try {
      await complaintsApi.process(id)
      await loadComplaint(id)
    } catch (err) {
      console.error('Pipeline processing failed:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id) return
    setIsSubmittingReview(true)
    setReviewSuccess(false)
    try {
      const draft = await complaintsApi.generateDraft(id, 'template')
      await reviewsApi.record(draft.id, reviewAction, reviewNotes)
      await loadComplaint(id)
      setReviewNotes('')
      setReviewSuccess(true)
    } catch (err) {
      console.error('Review record failed:', err)
    } finally {
      setIsSubmittingReview(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading case docket and intelligence modules..." />
  }

  if (!complaint) {
    return (
      <div className="p-12 text-center text-xs text-slate-400">
        Case record not found or inaccessible under current security credentials.
      </div>
    )
  }

  const rawOrExtractedText = complaint.extracted_text || complaint.raw_text || ''

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <Link to="/cases" className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors">
          Case Registry
        </Link>
        <ChevronRight className="h-3 w-3 text-slate-400" />
        <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
          {complaint.reference_id}
        </span>
      </div>

      {/* Case Header Card */}
      <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/60 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">
                  {complaint.reference_id}
                </span>
                <StatusBadge status={complaint.status} />
              </div>

              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                {complaint.title}
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400 pt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" /> Incident Date:{' '}
                  <strong className="text-slate-700 dark:text-slate-300 font-medium">
                    {complaint.incident_date || 'Unspecified in Statement'}
                  </strong>
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5 text-slate-400" /> Location:{' '}
                  <strong className="text-slate-700 dark:text-slate-300 font-medium">
                    {complaint.incident_location || 'Pending Jurisdiction'}
                  </strong>
                </span>
                <span className="flex items-center gap-1 font-mono text-[11px]">
                  Docket Created: {new Date(complaint.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRunProcessing}
                disabled={isProcessing}
                className="h-8 gap-1.5 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <RotateCw className={`h-3 w-3 ${isProcessing ? 'animate-spin' : ''}`} />
                <span>{isProcessing ? 'Processing...' : 'Reprocess Pipeline'}</span>
              </Button>

              <Link to={`/cases/${complaint.id}/evidence`}>
                <Button
                  variant="primary"
                  size="sm"
                  className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white shadow-2xs font-medium"
                >
                  <span>Evidence Workspace</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3 Pipeline Hub Gateway Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Hub 1: Evidence Provenance */}
        <Link to={`/cases/${complaint.id}/evidence`} className="block group">
          <Card className="h-full border-slate-200 dark:border-slate-800 group-hover:border-blue-500/60 dark:group-hover:border-blue-500/60 transition-all shadow-2xs bg-white dark:bg-slate-900/90">
            <CardContent className="p-5 flex flex-col justify-between h-full">
              <div className="space-y-2">
                <div className="h-8 w-8 rounded-lg bg-blue-50 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
                  <FileText className="h-4 w-4" />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                  1. Evidence Provenance
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Interactive split-screen viewer linking extracted named entities and facts to exact character offsets.
                </p>
              </div>
              <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold mt-4 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                Inspect Grounded Spans →
              </span>
            </CardContent>
          </Card>
        </Link>

        {/* Hub 2: FIR Draft */}
        <Link to={`/cases/${complaint.id}/draft`} className="block group">
          <Card className="h-full border-slate-200 dark:border-slate-800 group-hover:border-indigo-500/60 dark:group-hover:border-indigo-500/60 transition-all shadow-2xs bg-white dark:bg-slate-900/90">
            <CardContent className="p-5 flex flex-col justify-between h-full">
              <div className="space-y-2">
                <div className="h-8 w-8 rounded-lg bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                  <FileEdit className="h-4 w-4" />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                  2. FIR Draft Generator
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Compile, revise, version-control, and export structured legal drafts to PDF or DOCX formats.
                </p>
              </div>
              <span className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold mt-4 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                Open Draft Workspace →
              </span>
            </CardContent>
          </Card>
        </Link>

        {/* Hub 3: Factual Validation */}
        <Link to={`/cases/${complaint.id}/validation`} className="block group">
          <Card className="h-full border-slate-200 dark:border-slate-800 group-hover:border-amber-500/60 dark:group-hover:border-amber-500/60 transition-all shadow-2xs bg-white dark:bg-slate-900/90">
            <CardContent className="p-5 flex flex-col justify-between h-full">
              <div className="space-y-2">
                <div className="h-8 w-8 rounded-lg bg-amber-50 dark:bg-amber-950 flex items-center justify-center text-amber-600 dark:text-amber-400">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                  3. Factual Validation Report
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Automated detection of unsupported claims, temporal contradictions, and omitted elements.
                </p>
              </div>
              <span className="text-xs text-amber-600 dark:text-amber-400 font-semibold mt-4 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                Review Verification Flags →
              </span>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Citizen Complaint Statement Display */}
      <Card className="border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
        <CardHeader className="pb-3 pt-4 px-6 border-b border-slate-100 dark:border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
              Primary Recorded Complaint Narrative
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Source text utilized for entity extraction and factual grounding checks
            </CardDescription>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            {rawOrExtractedText.length} Characters • {rawOrExtractedText.split(/\s+/).length} Words
          </span>
        </CardHeader>
        <CardContent className="p-6">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-sans text-xs leading-relaxed text-slate-800 dark:text-slate-200 whitespace-pre-wrap select-text">
            {rawOrExtractedText}
          </div>
        </CardContent>
      </Card>

      {/* Supervisory Officer Review Form */}
      <Card className="border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
        <CardHeader className="pb-3 pt-4 px-6 border-b border-slate-100 dark:border-slate-800">
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Lock className="h-3.5 w-3.5 text-blue-500" />
            Supervisory Officer Audit & Sign-off Gate
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Officially commit supervisory determination to the permanent audit ledger.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          {reviewSuccess && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span>Review decision committed successfully to case audit log.</span>
            </div>
          )}

          <form onSubmit={handleReviewSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Supervisory Action
              </label>
              <select
                className="h-9 w-full px-3 rounded-md border border-slate-200 dark:border-slate-800 text-xs bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200 focus:outline-none"
                value={reviewAction}
                onChange={(e) => setReviewAction(e.target.value)}
              >
                <option value="approved">Approve Draft — Proceed to Official FIR Registration</option>
                <option value="clarification_requested">Request Further Complainant Clarification</option>
                <option value="edited">Edited / Amended by Supervisory Officer</option>
                <option value="rejected">Reject Draft / Insufficient Evidentiary Substance</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Supervisory Observation Notes
              </label>
              <textarea
                rows={3}
                placeholder="Document grounds for decision, witness interview instructions, or forensic follow-up..."
                className="w-full p-2.5 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200 focus:outline-none leading-relaxed"
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isSubmittingReview}
              className="h-9 px-4 gap-2 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>{isSubmittingReview ? 'Committing Decision...' : 'Record Official Determination'}</span>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
