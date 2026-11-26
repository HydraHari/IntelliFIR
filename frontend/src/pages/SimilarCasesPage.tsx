import React, { useState } from 'react'
import {
  Search,
  Layers,
  FileText,
  Plus,
  CheckCircle2,
  AlertCircle,
  ArrowUpRight,
  SlidersHorizontal,
  Sparkles,
  Cpu,
  ChevronRight,
  BookOpen,
} from 'lucide-react'
import { similarCasesApi, type SimilarCase } from '../api/similar_cases'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Textarea } from '../components/ui/textarea'
import { Progress } from '../components/ui/progress'
import { Badge } from '../components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog'
import { LoadingSpinner, EmptyState } from '../components/common/UIStates'

export const SimilarCasesPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SimilarCase[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [threshold, setThreshold] = useState(0.4)

  // Ingest Form State
  const [isIngestOpen, setIsIngestOpen] = useState(false)
  const [newRef, setNewRef] = useState('')
  const [newSummary, setNewSummary] = useState('')
  const [newCategory, setNewCategory] = useState('Theft / Burglary')
  const [isIngesting, setIsIngesting] = useState(false)
  const [ingestSuccess, setIngestSuccess] = useState(false)

  const handleSearch = async (e?: React.FormEvent, searchQuery?: string) => {
    if (e) e.preventDefault()
    const activeQuery = searchQuery !== undefined ? searchQuery : query
    if (!activeQuery.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const resp = await similarCasesApi.search(activeQuery, 5, threshold)
      setResults(resp.results || [])
    } catch (err) {
      console.error('Similar case search failed:', err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handlePresetClick = (preset: string) => {
    setQuery(preset)
    handleSearch(undefined, preset)
  }

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsIngesting(true)
    try {
      await similarCasesApi.ingest({
        reference_id: newRef,
        summary: newSummary,
        category: newCategory,
      })
      setIngestSuccess(true)
      setTimeout(() => {
        setIsIngestOpen(false)
        setIngestSuccess(false)
        setNewRef('')
        setNewSummary('')
      }, 1500)
    } catch (err) {
      console.error('Failed to ingest case:', err)
    } finally {
      setIsIngesting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Semantic Precedent Retrieval
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              FAISS Dense Vector
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Identify pattern modus operandi and related historic FIRs using Sentence-Transformers embeddings.
          </p>
        </div>

        <Dialog open={isIngestOpen} onOpenChange={setIsIngestOpen}>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Index Historic Docket</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <DialogHeader>
              <DialogTitle className="text-sm font-bold text-slate-900 dark:text-white">
                Index Historical Precedent into FAISS
              </DialogTitle>
            </DialogHeader>
            {ingestSuccess ? (
              <div className="p-6 text-center text-emerald-600 dark:text-emerald-400 flex flex-col items-center gap-2">
                <CheckCircle2 className="h-8 w-8" />
                <p className="text-xs font-semibold">
                  Case successfully vectorized and added to local FAISS index.
                </p>
              </div>
            ) : (
              <form onSubmit={handleIngest} className="space-y-3.5 pt-2">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Case Reference Number *
                  </label>
                  <Input
                    placeholder="e.g. FIR-2025-DL-882"
                    value={newRef}
                    onChange={(e) => setNewRef(e.target.value)}
                    className="h-8 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Offence Category
                  </label>
                  <Input
                    placeholder="e.g. Mobile Snatching / Street Robbery"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="h-8 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Case Summary / Modus Operandi *
                  </label>
                  <Textarea
                    rows={4}
                    placeholder="Describe facts, modus operandi, weapon used, time of day, getaway vehicle..."
                    value={newSummary}
                    onChange={(e) => setNewSummary(e.target.value)}
                    className="text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  variant="primary"
                  className="w-full h-9 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
                  disabled={isIngesting}
                >
                  {isIngesting ? 'Computing Embeddings...' : 'Vectorize & Commit to Index'}
                </Button>
              </form>
            )}
          </DialogContent>
        </Dialog>
      </div>

      {/* Semantic Search Box Card */}
      <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
        <CardContent className="p-4 space-y-3">
          <form onSubmit={handleSearch} className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Describe crime modus operandi, weapons, time, or location (e.g., 'motorcycle rider snatched phone at knife-point')..."
                className="pl-10 h-10 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            {/* Suggested Search Prompts */}
            <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
                Try:
              </span>
              {[
                'Two men on motorcycle snatched iPhone at knife-point',
                'Fake bank KYC SMS phishing transfer unauthorized debit',
                'Broken main door wooden latch stolen gold ornaments',
              ].map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handlePresetClick(p)}
                  className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors truncate max-w-xs"
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Threshold & Submit */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2.5 text-xs text-slate-500">
                <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
                <span>Cosine Cutoff:</span>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-24 accent-blue-600"
                />
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-300 text-[11px]">
                  {(threshold * 100).toFixed(0)}%
                </span>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={loading}
                className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
              >
                <Search className="h-3 w-3" />
                <span>{loading ? 'Embedding & Searching...' : 'Retrieve Precedents'}</span>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results Section */}
      <div className="space-y-3">
        {loading ? (
          <LoadingSpinner label="Running all-MiniLM-L6-v2 embeddings & FAISS search..." />
        ) : searched && results.length === 0 ? (
          <EmptyState
            title="No precedent cases exceeded similarity cutoff"
            description="Try lowering the cosine cutoff slider or adjusting search terminology to match broader incident patterns."
          />
        ) : !searched ? (
          <div className="text-center py-12 px-4 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl bg-white/40 dark:bg-slate-900/30 text-xs text-slate-400">
            Submit a query above or click a sample prompt to perform dense vector similarity retrieval against precedent dockets.
          </div>
        ) : (
          results.map((c) => {
            const pct = Math.round(c.score * 100)
            return (
              <Card
                key={c.id}
                className="border-slate-200/90 dark:border-slate-800 shadow-2xs hover:border-blue-400/60 dark:hover:border-blue-500/60 transition-colors bg-white dark:bg-slate-900/90"
              >
                <CardContent className="p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/60 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">
                        {c.reference_id}
                      </span>
                      {c.category && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                          {c.category}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-blue-600 dark:text-blue-400 font-mono">
                        {pct}% Match
                      </span>
                      <div className="w-16">
                        <Progress value={pct} className="h-1.5" />
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed">
                    {c.summary}
                  </p>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span>FAISS Dense Vector Match</span>
                    <span>Cosine Similarity: {c.score.toFixed(4)}</span>
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
