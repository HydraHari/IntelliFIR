import React, { useState } from 'react'
import {
  Bot,
  Send,
  User,
  BookOpen,
  AlertCircle,
  Sparkles,
  ShieldAlert,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  FileText,
  CornerDownLeft,
  X,
} from 'lucide-react'
import { assistantApi, type AssistantQueryResponse } from '../api/assistant'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{ title: string; content: string; score?: number }>
  citations?: string[]
  isRetrievalOnly?: boolean
}

export const AssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Greetings Officer. I am your Retrieval-Augmented Investigation Assistant. ' +
        'You can query complaint dockets, missing statutory elements, applicable sections of the Bharatiya Nyaya Sanhita (BNS) 2023, or precedent modus operandi.\n\n' +
        'Every answer is grounded strictly in indexed case documents and verified statutory provisions.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedSource, setSelectedSource] = useState<{
    title: string
    content: string
    score?: number
  } | null>(null)

  const handleSend = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault()
    const queryToSend = customQuery !== undefined ? customQuery : input
    if (!queryToSend.trim() || loading) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: queryToSend,
    }

    setMessages((prev) => [...prev, userMsg])
    if (customQuery === undefined) setInput('')
    setLoading(true)

    try {
      const resp = await assistantApi.query({ question: userMsg.content })
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: resp.answer,
        sources: resp.sources,
        citations: resp.citations,
        isRetrievalOnly: resp.is_retrieval_only,
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content:
            'Service Alert: Unable to complete RAG query. Please check local Ollama or vector store connections.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const promptSuggestions = [
    'What are the essential legal ingredients required for Section 303 (Theft)?',
    'Which penal code section applies to financial cheating via SMS phishing link?',
    'Explain the legal difference between Theft (Sec 303) and Robbery (Sec 309).',
  ]

  return (
    <div className="max-w-6xl mx-auto h-[calc(100vh-130px)] flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-200/80 dark:border-slate-800/80 flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span>Investigative Intelligence Assistant (RAG)</span>
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              Grounded AI
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Strict evidence grounding with automatic document retrieval and provenance citations.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>FAISS Vector Engine Active</span>
        </div>
      </div>

      {/* Main Chat & Source Inspector Grid (8 cols / 4 cols) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Chat Stream (8 cols) */}
        <Card className="lg:col-span-8 flex flex-col h-full overflow-hidden border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
          <CardContent className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-xs ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white flex-shrink-0 mt-0.5 shadow-2xs">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-xl p-3.5 leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-slate-50 dark:bg-slate-950 border border-slate-200/90 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none shadow-2xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>

                  {/* Retrieval Only Notice */}
                  {m.isRetrievalOnly && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/60 dark:border-slate-800 flex items-center gap-1.5 text-[10px] text-amber-700 dark:text-amber-400 font-medium">
                      <AlertCircle className="h-3 w-3" /> Dense Vector Retrieval Mode (Deterministic synthesis active)
                    </div>
                  )}

                  {/* Grounded Citation Chips */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-200/60 dark:border-slate-800 space-y-1.5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                        Retrieved Legal Grounds & Case Precedents:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {m.sources?.map((src, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setSelectedSource(src)}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/80 hover:bg-blue-50 transition-colors shadow-2xs"
                          >
                            <BookOpen className="h-2.5 w-2.5 text-blue-500" />
                            <span className="truncate max-w-[200px]">{src.title}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="h-7 w-7 rounded-lg bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 flex-shrink-0 mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
                <div className="h-2 w-2 rounded-full bg-blue-600 animate-ping" />
                <span>Retrieving statutory precedents and reasoning over facts...</span>
              </div>
            )}
          </CardContent>

          {/* Quick Suggestions & Input Bar */}
          <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 space-y-2">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {promptSuggestions.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(undefined, p)}
                  className="px-2 py-0.5 rounded text-[10px] font-medium bg-white dark:bg-slate-900 hover:bg-slate-100 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 whitespace-nowrap transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>

            <form onSubmit={handleSend} className="flex gap-2">
              <Input
                placeholder="Ask an investigative or legal question grounded in case evidence..."
                className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100"
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <Button
                type="submit"
                variant="primary"
                disabled={loading || !input.trim()}
                className="gap-1.5 text-xs h-9 px-3.5 bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-2xs"
              >
                <Send className="h-3 w-3" />
                <span>Send</span>
              </Button>
            </form>
          </div>
        </Card>

        {/* Source Inspector Panel (4 cols) */}
        <Card className="lg:col-span-4 flex flex-col h-full overflow-hidden border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
          <CardHeader className="py-2.5 px-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 flex-shrink-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <BookOpen className="h-3.5 w-3.5 text-blue-500" />
              Retrieved Source Inspector
            </CardTitle>
            {selectedSource && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedSource(null)}
                className="h-6 w-6 p-0 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </CardHeader>

          <CardContent className="flex-1 p-4 overflow-y-auto text-xs">
            {selectedSource ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-900 dark:text-slate-100 text-xs">
                    {selectedSource.title}
                  </h4>
                  {selectedSource.score !== undefined && (
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                      {(selectedSource.score * 100).toFixed(0)}% Match
                    </span>
                  )}
                </div>

                <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 font-sans text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {selectedSource.content}
                </div>

                <p className="text-[10px] text-slate-400 font-mono">
                  Grounding validated from local FAISS vector store.
                </p>
              </div>
            ) : (
              <div className="text-center py-20 text-slate-400 flex flex-col items-center gap-2">
                <BookOpen className="h-8 w-8 text-slate-300 dark:text-slate-700" />
                <p className="text-xs max-w-xs">
                  Click on any citation chip in the conversation to inspect the underlying statutory section or case evidence.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
