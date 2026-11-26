import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Shield,
  User,
  MapPin,
  Calendar,
  Clock,
  Sparkles,
  Layers,
  ArrowRight,
  X,
  Code2,
  Search,
  BookOpen,
} from 'lucide-react'
import { complaintsApi } from '../api/complaints'
import type { Complaint } from '../types/complaint'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import { LoadingSpinner } from '../components/common/UIStates'

interface EntityItem {
  id: string
  entity_text: string
  entity_type: string
  start_offset: number
  end_offset: number
  confidence?: number
  source_sentence?: string
}

interface FactItem {
  id: string
  fact_type: string
  fact_value: string
  source_text?: string
  is_certain: boolean
  confidence?: number
  evidence_spans: Array<{
    id: string
    original_text: string
    start_offset: number
    end_offset: number
  }>
}

export const EvidenceViewerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [complaint, setComplaint] = useState<Complaint | null>(null)
  const [entities, setEntities] = useState<EntityItem[]>([])
  const [facts, setFacts] = useState<FactItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSpan, setSelectedSpan] = useState<{
    start: number
    end: number
    text: string
    factType?: string
  } | null>(null)
  const [activeTab, setActiveTab] = useState<'facts' | 'entities' | 'structured'>('facts')
  const [entityFilter, setEntityFilter] = useState('')

  useEffect(() => {
    if (id) {
      loadData(id)
    }
  }, [id])

  const loadData = async (caseId: string) => {
    setLoading(true)
    try {
      const [compData, extData] = await Promise.all([
        complaintsApi.get(caseId),
        complaintsApi.getExtraction(caseId),
      ])
      setComplaint(compData)
      setEntities(extData.entities || [])
      setFacts(extData.facts || [])
    } catch (err) {
      console.error('Failed to load evidence viewer data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFactClick = (fact: FactItem) => {
    if (fact.evidence_spans && fact.evidence_spans.length > 0) {
      const span = fact.evidence_spans[0]
      setSelectedSpan({
        start: span.start_offset,
        end: span.end_offset,
        text: span.original_text,
        factType: fact.fact_type,
      })
    } else {
      setSelectedSpan(null)
    }
  }

  const handleEntityClick = (ent: EntityItem) => {
    setSelectedSpan({
      start: ent.start_offset,
      end: ent.end_offset,
      text: ent.entity_text,
      factType: ent.entity_type,
    })
  }

  if (loading) {
    return <LoadingSpinner label="Loading document text and evidence provenance offsets..." />
  }

  if (!complaint) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Complaint record not found.
      </div>
    )
  }

  const originalText = complaint.extracted_text || complaint.raw_text || ''

  // Function to render text with highlighted active selected span
  const renderHighlightedText = () => {
    if (!selectedSpan || selectedSpan.start === undefined || selectedSpan.end === undefined) {
      return <span>{originalText}</span>
    }

    const { start, end } = selectedSpan
    if (start < 0 || end > originalText.length || start >= end) {
      return <span>{originalText}</span>
    }

    const before = originalText.slice(0, start)
    const highlighted = originalText.slice(start, end)
    const after = originalText.slice(end)

    return (
      <>
        <span>{before}</span>
        <mark className="bg-amber-300 dark:bg-amber-400/90 text-slate-900 font-semibold px-1 py-0.5 rounded shadow-xs border border-amber-400 dark:border-amber-500 evidence-target-active">
          {highlighted}
        </mark>
        <span>{after}</span>
      </>
    )
  }

  const filteredEntities = entities.filter((e) =>
    entityFilter ? e.entity_type.toLowerCase() === entityFilter.toLowerCase() : true
  )

  const entityTypes = Array.from(new Set(entities.map((e) => e.entity_type)))

  return (
    <div className="space-y-4">
      {/* Navigation Breadcrumb */}
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
            Evidence Provenance Inspector
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Link to={`/cases/${complaint.id}/draft`}>
            <Button
              variant="primary"
              size="sm"
              className="h-7 text-xs gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium"
            >
              <span>View FIR Draft</span>
              <ExternalLink className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Docket Header Strip */}
      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider bg-slate-800 px-2 py-0.5 rounded text-blue-300 border border-slate-700">
              {complaint.reference_id}
            </span>
            <span className="text-xs font-semibold text-slate-100 truncate">
              {complaint.title}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Character-level grounding linking FIR claims directly to the complainant's statements.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="text-right">
            <span className="text-slate-400 block text-[9px] uppercase tracking-wider">
              Token Entities
            </span>
            <span className="font-bold text-white text-sm">{entities.length}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div className="text-right">
            <span className="text-slate-400 block text-[9px] uppercase tracking-wider">
              Grounded Facts
            </span>
            <span className="font-bold text-white text-sm">{facts.length}</span>
          </div>
        </div>
      </div>

      {/* Split-Screen Workspace (7 Cols Left / 5 Cols Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-[calc(100vh-220px)] min-h-[520px]">
        {/* Left Panel: Primary Statement with Live Highlighting */}
        <Card className="lg:col-span-7 flex flex-col h-full overflow-hidden border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
          <CardHeader className="py-2.5 px-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 flex-shrink-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 text-blue-500" />
              Source Complaint Document (Raw Transcribed Text)
            </CardTitle>

            {selectedSpan && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedSpan(null)}
                className="h-6 text-[10px] px-2 text-slate-400 hover:text-slate-600 gap-1"
              >
                <X className="h-3 w-3" /> Clear Span
              </Button>
            )}
          </CardHeader>

          <CardContent className="flex-1 p-5 overflow-y-auto font-sans text-xs leading-relaxed text-slate-800 dark:text-slate-200 whitespace-pre-wrap select-text">
            {renderHighlightedText()}
          </CardContent>

          {/* Active Highlight Banner */}
          {selectedSpan && (
            <div className="p-2.5 bg-amber-50 dark:bg-amber-950/40 border-t border-amber-200 dark:border-amber-800/60 text-xs text-amber-900 dark:text-amber-300 flex items-center justify-between">
              <span className="font-mono text-[11px] truncate max-w-sm">
                Target Evidence: "{selectedSpan.text}"
              </span>
              <span className="text-[10px] font-mono font-semibold uppercase bg-amber-200 dark:bg-amber-900 px-2 py-0.5 rounded text-amber-900 dark:text-amber-100">
                Offsets [{selectedSpan.start}:{selectedSpan.end}]
              </span>
            </div>
          )}
        </Card>

        {/* Right Panel: Extracted Intelligence Hub */}
        <Card className="lg:col-span-5 flex flex-col h-full overflow-hidden border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
          <CardHeader className="p-2 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 flex-shrink-0">
            <Tabs
              value={activeTab}
              onValueChange={(v) => setActiveTab(v as any)}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3 p-1 bg-slate-200/60 dark:bg-slate-800/60 rounded-lg">
                <TabsTrigger value="facts" className="text-xs font-medium">
                  Facts ({facts.length})
                </TabsTrigger>
                <TabsTrigger value="entities" className="text-xs font-medium">
                  Entities ({entities.length})
                </TabsTrigger>
                <TabsTrigger value="structured" className="text-xs font-medium">
                  JSON Schema
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>

          <CardContent className="flex-1 p-3.5 overflow-y-auto space-y-2.5">
            {activeTab === 'facts' && (
              <div className="space-y-2">
                {facts.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-12">
                    No structured facts extracted for this docket.
                  </p>
                ) : (
                  facts.map((fact) => {
                    const hasSpan = fact.evidence_spans && fact.evidence_spans.length > 0
                    const isSelected =
                      hasSpan &&
                      selectedSpan?.start === fact.evidence_spans[0].start_offset

                    return (
                      <div
                        key={fact.id}
                        onClick={() => handleFactClick(fact)}
                        className={`p-3 rounded-lg border text-xs transition-all cursor-pointer ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50/60 dark:bg-blue-950/50 ring-1 ring-blue-500/30'
                            : hasSpan
                            ? 'border-slate-200 dark:border-slate-800 hover:border-blue-400/60 hover:bg-slate-50 dark:hover:bg-slate-800/40'
                            : 'border-amber-200/80 dark:border-amber-900/50 bg-amber-50/30 dark:bg-amber-950/20'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-bold text-slate-700 dark:text-slate-300 uppercase text-[10px] tracking-wider">
                            {fact.fact_type.replace(/_/g, ' ')}
                          </span>
                          {fact.is_certain ? (
                            <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 px-1.5 py-0.2 rounded">
                              <CheckCircle2 className="h-2.5 w-2.5" /> Direct Fact
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 px-1.5 py-0.2 rounded">
                              <AlertTriangle className="h-2.5 w-2.5" /> Complainant Belief
                            </span>
                          )}
                        </div>

                        <p className="font-medium text-slate-900 dark:text-slate-100 text-xs leading-snug">
                          {fact.fact_value}
                        </p>

                        <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px]">
                          {hasSpan ? (
                            <span className="text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center gap-1 text-[11px]">
                              Inspect Highlight Span →
                            </span>
                          ) : (
                            <span className="text-amber-600 dark:text-amber-400 flex items-center gap-1 font-medium text-[11px]">
                              <AlertTriangle className="h-3 w-3" /> Unlinked Claim
                            </span>
                          )}

                          {fact.confidence && (
                            <span className="text-slate-400 font-mono text-[10px]">
                              {(fact.confidence * 100).toFixed(0)}% conf
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            )}

            {activeTab === 'entities' && (
              <div className="space-y-2">
                {/* Filter bar for entities */}
                {entityTypes.length > 0 && (
                  <div className="flex items-center gap-1.5 pb-2 overflow-x-auto">
                    <button
                      type="button"
                      onClick={() => setEntityFilter('')}
                      className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                        entityFilter === ''
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700'
                      }`}
                    >
                      All ({entities.length})
                    </button>
                    {entityTypes.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setEntityFilter(t)}
                        className={`px-2 py-0.5 rounded text-[10px] font-medium border uppercase ${
                          entityFilter === t
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700'
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                )}

                {filteredEntities.map((ent) => {
                  const isSelected = selectedSpan?.start === ent.start_offset

                  return (
                    <div
                      key={ent.id}
                      onClick={() => handleEntityClick(ent)}
                      className={`p-2.5 rounded-lg border text-xs flex items-center justify-between cursor-pointer transition-colors ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50/60 dark:bg-blue-950/50'
                          : 'border-slate-200 dark:border-slate-800 hover:border-blue-400/60 hover:bg-slate-50 dark:hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          {ent.entity_text}
                        </span>
                        <span className="font-mono text-[10px] text-slate-400">
                          [{ent.start_offset}:{ent.end_offset}]
                        </span>
                      </div>
                      <span className="text-[9px] font-mono uppercase font-bold px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                        {ent.entity_type}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}

            {activeTab === 'structured' && (
              <pre className="text-[11px] font-mono bg-slate-950 text-emerald-400 p-3 rounded-lg overflow-x-auto border border-slate-800 leading-snug">
                {JSON.stringify(complaint.structured_data || {}, null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
