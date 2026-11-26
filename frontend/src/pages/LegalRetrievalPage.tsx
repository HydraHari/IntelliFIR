import React, { useState, useEffect } from 'react'
import {
  Scale,
  Search,
  Plus,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  ShieldAlert,
  ChevronRight,
  Sparkles,
  FileText,
} from 'lucide-react'
import { legalApi, type LegalSearchResult, type LegalDocument } from '../api/legal'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Textarea } from '../components/ui/textarea'
import { Badge } from '../components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog'
import { LoadingSpinner, EmptyState } from '../components/common/UIStates'

export const LegalRetrievalPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LegalSearchResult[]>([])
  const [documents, setDocuments] = useState<LegalDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  // Ingest Form
  const [isOpen, setIsOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [source, setSource] = useState('Bharatiya Nyaya Sanhita, 2023')
  const [content, setContent] = useState('')
  const [provType, setProvType] = useState('penal_code')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const docs = await legalApi.listDocuments()
      setDocuments(docs || [])
    } catch (err) {
      console.error('Failed to load legal documents:', err)
    }
  }

  const handleSearch = async (e?: React.FormEvent, searchQuery?: string) => {
    if (e) e.preventDefault()
    const activeQuery = searchQuery !== undefined ? searchQuery : query
    if (!activeQuery.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const data = await legalApi.search(activeQuery, 5)
      setResults(data || [])
    } catch (err) {
      console.error('Legal search failed:', err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handlePresetClick = (preset: string) => {
    setQuery(preset)
    handleSearch(undefined, preset)
  }

  const handleAddDocument = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await legalApi.addDocument({
        title,
        source,
        content,
        provision_type: provType,
      })
      setIsOpen(false)
      setTitle('')
      setContent('')
      loadDocuments()
    } catch (err) {
      console.error('Failed to add legal doc:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Verified Statutory Knowledgebase
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              Zero Hallucination
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Semantic search across verified statutory penal provisions (BNS 2023, IT Act, BNSS).
          </p>
        </div>

        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Index New Statute</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
            <DialogHeader>
              <DialogTitle className="text-sm font-bold text-slate-900 dark:text-white">
                Add Verified Statutory Provision
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddDocument} className="space-y-3.5 pt-2">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Provision Section & Title *
                </label>
                <Input
                  placeholder="e.g. BNS Section 303 (Theft)"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="h-8 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Source Code / Act *
                </label>
                <Input
                  placeholder="e.g. Bharatiya Nyaya Sanhita, 2023"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="h-8 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Verbatim Statutory Provisions Text *
                </label>
                <Textarea
                  rows={5}
                  placeholder="Paste verified text of statute, legal ingredients, definition, and punishment..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800"
                  required
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full h-9 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Vectorizing and Indexing...' : 'Index Verified Legal Text'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search Input Box */}
      <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
        <CardContent className="p-4 space-y-3">
          <form onSubmit={handleSearch} className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search legal provision (e.g., 'theft of movable property without consent', 'cheating by personation over computer resource')..."
                className="pl-10 h-10 text-xs bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            {/* Suggested Prompts */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
                Suggested Sections:
              </span>
              {[
                'Taking movable property without consent theft',
                'Robbery with threat of instant death or hurt',
                'Cheating by personation using computer resource SMS phishing',
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

            <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
              <span className="text-[11px] text-slate-400">
                Grounding against official statutes indexed in FAISS
              </span>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={loading}
                className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
              >
                <Scale className="h-3.5 w-3.5" />
                <span>{loading ? 'Searching...' : 'Search Statutes'}</span>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results / List */}
      <div className="space-y-3">
        {loading ? (
          <LoadingSpinner label="Searching verified legal statutes in vector index..." />
        ) : searched && results.length === 0 ? (
          <EmptyState
            title="No matching legal provisions found"
            description="No indexed statutes exceeded the semantic relevance threshold for this query. You can add new verified legal provisions using the button above."
          />
        ) : searched ? (
          results.map((res) => (
            <Card
              key={res.id}
              className="border-slate-200/90 dark:border-slate-800 shadow-2xs hover:border-blue-400/60 dark:hover:border-blue-500/60 transition-colors bg-white dark:bg-slate-900/90"
            >
              <CardContent className="p-4 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      {res.title}
                    </h3>
                    <p className="text-[11px] text-slate-400">{res.source}</p>
                  </div>
                  <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">
                    {(res.score * 100).toFixed(0)}% Relevance
                  </span>
                </div>

                <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 font-sans text-xs text-slate-800 dark:text-slate-200 leading-relaxed">
                  {res.snippet}
                </div>

                <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                  <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium">
                    <ShieldAlert className="h-3 w-3" /> Reference only • Requires officer confirmation
                  </span>
                  <span className="uppercase font-semibold px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                    {res.provision_type}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          /* Initial view: Indexed database */
          <div className="space-y-2.5">
            <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Currently Indexed Statutory Provisions ({documents.length})
            </h3>
            {documents.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900">
                No legal documents currently indexed. Add provisions above to enable grounded penal retrieval.
              </div>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3.5 rounded-lg border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900/90 flex items-center justify-between shadow-2xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-md bg-blue-50 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
                      <BookOpen className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                        {doc.title}
                      </p>
                      <p className="text-[11px] text-slate-400">{doc.source}</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                    {doc.provision_type}
                  </span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
