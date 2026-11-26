import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  FileText,
  FileDown,
  Edit3,
  Save,
  X,
  RotateCw,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Printer,
  Eye,
  FileCheck2,
} from 'lucide-react'
import { draftsApi } from '../api/drafts'
import { complaintsApi } from '../api/complaints'
import type { FIRDraft } from '../types/draft'
import type { Complaint } from '../types/complaint'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Textarea } from '../components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert'
import { LoadingSpinner } from '../components/common/UIStates'

export const DraftPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [complaint, setComplaint] = useState<Complaint | null>(null)
  const [draft, setDraft] = useState<FIRDraft | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    if (id) {
      loadDraftData(id)
    }
  }, [id])

  const loadDraftData = async (caseId: string) => {
    setLoading(true)
    try {
      const comp = await complaintsApi.get(caseId)
      setComplaint(comp)

      try {
        const draftData = await draftsApi.getForComplaint(caseId)
        setDraft(draftData)
        setEditContent(draftData.content)
      } catch (e) {
        setDraft(null)
      }
    } catch (err) {
      console.error('Failed to load draft:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async (method: string = 'template') => {
    if (!id) return
    setIsGenerating(true)
    try {
      const newDraft = await draftsApi.generate(id, method)
      setDraft(newDraft)
      setEditContent(newDraft.content)
    } catch (err) {
      console.error('Draft generation failed:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSaveEdit = async () => {
    if (!draft) return
    try {
      const updated = await draftsApi.update(draft.id, { content: editContent })
      setDraft(updated)
      setIsEditing(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('Failed to save draft edits:', err)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Retrieving FIR Draft legal docket..." />
  }

  if (!complaint) {
    return <p className="text-center p-8 text-xs text-slate-400">Case docket not found.</p>
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Breadcrumb & Top Actions */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Link to="/cases" className="hover:text-slate-800 dark:hover:text-slate-200">
            Cases
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-400" />
          <Link
            to={`/cases/${complaint.id}`}
            className="hover:text-slate-800 dark:hover:text-slate-200 font-mono"
          >
            {complaint.reference_id}
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-400" />
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            First Information Report Draft
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Link to={`/cases/${complaint.id}/evidence`}>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300"
            >
              <span>Evidence Provenance</span>
            </Button>
          </Link>
          {draft && (
            <Link to={`/cases/${complaint.id}/validation`}>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800/60 bg-amber-50/50 dark:bg-amber-950/20"
              >
                <AlertTriangle className="h-3 w-3" />
                <span>Validation Audit</span>
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Mandatory Statutory Notice */}
      <div className="p-3.5 rounded-xl border-l-4 border-l-amber-500 bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-900/50 text-amber-950 dark:text-amber-200 flex items-start gap-3 shadow-2xs">
        <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 dark:text-amber-300">
            AI-Generated Draft — Requires Authorized Human Review & Signature
          </h4>
          <p className="text-[11px] leading-relaxed text-amber-800 dark:text-amber-300/80">
            This preliminary FIR draft was compiled algorithmically from the citizen's statement. It does not establish legal guilt, make final judicial determinations, or constitute an officially registered FIR without the signature and seal of the authorized Station House Officer.
          </p>
        </div>
      </div>

      {saveSuccess && (
        <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          <span>Draft modifications saved successfully and logged in system audit ledger.</span>
        </div>
      )}

      {/* Empty State vs Document Card */}
      {!draft ? (
        <Card className="text-center p-12 border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
          <div className="flex flex-col items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <FileText className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              No Preliminary Draft Generated Yet
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md leading-relaxed">
              Synthesize a factually grounded legal draft using the extracted facts. Controlled template synthesis is the validated deterministic default.
            </p>
            <div className="flex items-center gap-3 mt-4">
              <Button
                variant="primary"
                onClick={() => handleGenerate('template')}
                disabled={isGenerating}
                className="gap-2 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{isGenerating ? 'Synthesizing...' : 'Generate Grounded FIR Draft'}</span>
              </Button>
              <Button
                variant="outline"
                onClick={() => handleGenerate('llm')}
                disabled={isGenerating}
                className="gap-2 text-xs border-slate-200 dark:border-slate-800"
              >
                <span>Generate via Ollama LLM</span>
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90 overflow-hidden">
          {/* Action Toolbar */}
          <div className="px-5 py-3 border-b border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                Draft Version {draft.version}
              </span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="text-[11px] text-slate-500 font-mono capitalize">
                Method: {(draft as any).generation_method || 'Controlled Template'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsEditing(false)
                      setEditContent(draft.content)
                    }}
                    className="h-7 text-xs border-slate-200 dark:border-slate-800"
                  >
                    <X className="h-3 w-3 mr-1" />
                    <span>Cancel</span>
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleSaveEdit}
                    className="h-7 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
                  >
                    <Save className="h-3 w-3 mr-1" />
                    <span>Save Amendments</span>
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                    className="h-7 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300"
                  >
                    <Edit3 className="h-3 w-3 mr-1 text-slate-400" />
                    <span>Edit Draft</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleGenerate('template')}
                    disabled={isGenerating}
                    className="h-7 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300"
                  >
                    <RotateCw className={`h-3 w-3 mr-1 ${isGenerating ? 'animate-spin' : ''}`} />
                    <span>Regenerate</span>
                  </Button>
                  <a
                    href={draftsApi.exportDocxUrl(draft.id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Button
                      variant="primary"
                      size="sm"
                      className="h-7 text-xs gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium"
                    >
                      <FileDown className="h-3 w-3" />
                      <span>Export DOCX</span>
                    </Button>
                  </a>
                </>
              )}
            </div>
          </div>

          {/* Legal Document Container */}
          <CardContent className="p-8 lg:p-10 bg-slate-50/40 dark:bg-slate-950/40">
            {isEditing ? (
              <div className="space-y-2">
                <Textarea
                  rows={24}
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="font-mono text-xs leading-relaxed bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 p-4"
                />
              </div>
            ) : (
              <div className="max-w-3xl mx-auto bg-white dark:bg-slate-900 p-8 sm:p-12 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
                {/* Official Legal Document Header */}
                <div className="text-center pb-6 border-b-2 border-slate-800 dark:border-slate-200 space-y-1">
                  <p className="text-[11px] font-mono tracking-widest uppercase font-bold text-slate-500">
                    Form No. 1 • Police Station Investigation Docket
                  </p>
                  <h2 className="text-lg font-serif font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                    First Information Report (Preliminary Draft)
                  </h2>
                  <p className="text-[10px] text-slate-400 italic">
                    (Recorded under Section 173 of the Bharatiya Nagarik Suraksha Sanhita, 2023)
                  </p>
                </div>

                {/* Preformatted Legal Text */}
                <pre className="font-mono text-xs leading-relaxed text-slate-800 dark:text-slate-200 whitespace-pre-wrap select-text">
                  {draft.content}
                </pre>

                {/* Signature Gate */}
                <div className="pt-8 border-t border-slate-200 dark:border-slate-800 grid grid-cols-2 gap-8 text-xs text-slate-500">
                  <div className="space-y-6">
                    <p className="font-semibold">Complainant / Informant Signature:</p>
                    <div className="h-10 border-b border-dashed border-slate-300 dark:border-slate-700" />
                    <p className="text-[10px] text-slate-400">Thumb impression / Written Mark</p>
                  </div>
                  <div className="space-y-6 text-right">
                    <p className="font-semibold">Station House Officer Signature & Stamp:</p>
                    <div className="h-10 border-b border-dashed border-slate-300 dark:border-slate-700" />
                    <p className="text-[10px] text-slate-400">Rank & Police Precinct Seal</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
