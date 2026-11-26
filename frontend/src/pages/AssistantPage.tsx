import React, { useEffect, useState } from 'react'
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
  RefreshCw,
  Scale,
  Search,
  Clock,
  Cpu,
  Check,
  AlertTriangle,
  ArrowRight,
  Download,
  Copy,
  ExternalLink,
  HelpCircle,
  Activity,
  Layers,
  Database,
  CheckSquare,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  assistantApi,
  type AgentRunResponse,
  type CaseSummaryItem,
  type ToolExecutionRecord,
} from '../api/assistant'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  agentData?: AgentRunResponse
}

export const AssistantPage: React.FC = () => {
  // Available cases
  const [cases, setCases] = useState<CaseSummaryItem[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<string>('')
  const [activeTab, setActiveTab] = useState<string>('activity')

  // Conversation history
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Greetings Officer. I am your autonomous AI Investigation Agent for IntelliFIR.\n\n' +
        'I plan multi-step workflows, verify evidence provenance with strict character offsets, ' +
        'detect contradictions, retrieve verified provisions of the Bharatiya Nyaya Sanhita (BNS 2023), ' +
        'and generate structured investigation support summaries.\n\n' +
        'Select an indexed case docket or enter an investigative directive to begin.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestAgentData, setLatestAgentData] = useState<AgentRunResponse | null>(null)
  const [expandedToolIndex, setExpandedToolIndex] = useState<number | null>(null)

  // Fetch available cases on mount
  useEffect(() => {
    assistantApi
      .listCases()
      .then((data) => {
        setCases(data)
        if (data.length > 0 && !selectedCaseId) {
          setSelectedCaseId(data[0].reference_id)
        }
      })
      .catch((err) => {
        console.error('Failed to load complaint cases:', err)
      })
  }, [])

  const handleSend = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault()
    const queryToSend = customQuery !== undefined ? customQuery : input
    if (!queryToSend.trim() || loading) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: queryToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    if (customQuery === undefined) setInput('')
    setLoading(true)

    try {
      const resp = await assistantApi.agentRun({
        message: userMsg.content,
        complaint_id: selectedCaseId || undefined,
        history: messages.slice(-4).map((m) => ({ role: m.role, content: m.content })),
      })

      setLatestAgentData(resp)

      // Auto-switch right panel tab based on what was generated
      if (resp.investigation_report) {
        setActiveTab('report')
      } else if (resp.factual_validation || resp.complaint_analysis) {
        setActiveTab('findings')
      } else if (resp.legal_research) {
        setActiveTab('research')
      } else {
        setActiveTab('activity')
      }

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: resp.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        agentData: resp,
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err: any) {
      console.error('Investigation Agent run error:', err)
      toast.error('Agent execution error. Please check backend connection.')
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content:
            '❌ **Service Alert:** Unable to complete agent execution. ' +
            'Please verify your network connection and ensure the IntelliFIR backend is active.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const promptSuggestions = [
    selectedCaseId
      ? `Analyse complaint ${selectedCaseId}, identify contradictions, find relevant legal provisions and prepare an investigation summary.`
      : 'Analyse complaint CMP-001, identify contradictions, find relevant legal provisions and prepare an investigation summary.',
    'Check missing statutory elements, date/time gaps, and timeline contradictions.',
    'What are the essential legal ingredients for Theft under Section 303(2) BNS 2023?',
    'Find semantically similar precedent cases for vehicle theft outside market.',
  ]

  const handleCopyReport = () => {
    if (latestAgentData?.investigation_report?.formatted_markdown) {
      navigator.clipboard.writeText(latestAgentData.investigation_report.formatted_markdown)
      toast.success('Investigation Report copied to clipboard!')
    }
  }

  const handleDownloadReport = () => {
    if (latestAgentData?.investigation_report?.formatted_markdown) {
      const blob = new Blob([latestAgentData.investigation_report.formatted_markdown], {
        type: 'text/markdown;charset=utf-8',
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `investigation-report-${latestAgentData.investigation_report.case_identifier || 'case'}.md`
      link.click()
      URL.revokeObjectURL(url)
      toast.success('Investigation Report downloaded as Markdown.')
    }
  }

  return (
    <div className="max-w-[1600px] mx-auto h-[calc(100vh-115px)] flex flex-col gap-2.5">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800 gap-2 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                <span>AI Investigation Agent</span>
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-semibold">
                Autonomous Tool-Using Engine
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-semibold flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> BNS 2023 Statutory Grounded
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Evidence provenance verification, contradiction detection, statutory research, and investigation reports.
            </p>
          </div>
        </div>

        {/* Case Docket Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1">
            <Database className="h-3.5 w-3.5 text-blue-500" />
            <span>Target Docket:</span>
          </label>
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="text-xs font-mono h-8 px-2.5 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">-- No Case (General Legal Research) --</option>
            {cases.map((c) => (
              <option key={c.id} value={c.reference_id}>
                {c.reference_id} — {c.title.slice(0, 35)}
                {c.title.length > 35 ? '...' : ''}
              </option>
            ))}
          </select>
          {selectedCaseId && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedCaseId('')}
              className="h-8 px-2 text-[11px] text-slate-500 hover:text-slate-800"
              title="Clear docket selection"
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Main Split Layout: Left Conversation (45%) | Right Investigation Workspace (55%) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 overflow-hidden min-h-0">
        {/* ==================================================================== */}
        {/* PANEL A: CONVERSATION PANEL (5 COLS)                                 */}
        {/* ==================================================================== */}
        <Card className="lg:col-span-5 flex flex-col h-full overflow-hidden border-slate-200/90 dark:border-slate-800 shadow-sm bg-white dark:bg-slate-900/90">
          <CardHeader className="py-2.5 px-3.5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 flex-shrink-0 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-blue-600" />
              <CardTitle className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                Investigator Dialogue
              </CardTitle>
            </div>
            {selectedCaseId ? (
              <Badge variant="outline" className="text-[10px] font-mono bg-blue-50 text-blue-700 border-blue-200">
                Active: {selectedCaseId}
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px] font-mono text-slate-400">
                General Mode
              </Badge>
            )}
          </CardHeader>

          {/* Messages Stream */}
          <CardContent className="flex-1 p-3.5 overflow-y-auto space-y-3.5 text-xs">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-2.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="h-6 w-6 rounded-md bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white flex-shrink-0 mt-0.5">
                    <Bot className="h-3.5 w-3.5" />
                  </div>
                )}

                <div
                  className={`max-w-[88%] rounded-xl p-3 leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-slate-50 dark:bg-slate-950 border border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none shadow-xs'
                  }`}
                >
                  <div className="whitespace-pre-wrap leading-relaxed space-y-1">{m.content}</div>

                  {/* Safety Guardrail Alert if Consequential Action Blocked */}
                  {m.agentData?.requires_human_approval && (
                    <Alert className="mt-2.5 py-1.5 px-2.5 bg-amber-500/10 border-amber-500/30 text-amber-800 dark:text-amber-300">
                      <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
                      <AlertDescription className="text-[11px] leading-tight ml-1.5">
                        Consequential action safeguarded: Human approval mandatory under BNSS.
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Execution Badge in message */}
                  {m.agentData && m.agentData.tool_executions.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
                      <span className="flex items-center gap-1 font-mono">
                        <Activity className="h-3 w-3 text-emerald-500" />
                        {m.agentData.tool_executions.length} tools executed (
                        {m.agentData.tool_executions.reduce((acc, t) => acc + t.duration_ms, 0).toFixed(0)}ms)
                      </span>
                      <button
                        onClick={() => {
                          setLatestAgentData(m.agentData || null)
                          setActiveTab('activity')
                        }}
                        className="text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center gap-0.5"
                      >
                        <span>View Details</span>
                        <ChevronRight className="h-2.5 w-2.5" />
                      </button>
                    </div>
                  )}

                  <div className="text-[9px] text-slate-400 text-right mt-1 font-mono">{m.timestamp}</div>
                </div>

                {m.role === 'user' && (
                  <div className="h-6 w-6 rounded-md bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 flex-shrink-0 mt-0.5">
                    <User className="h-3.5 w-3.5" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 p-2 font-mono">
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Agent planning tasks, executing tools, and grounding findings...</span>
              </div>
            )}
          </CardContent>

          {/* Contextual Follow-Up Suggestions & Input Form */}
          <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 space-y-2">
            {/* Suggested Follow-Ups */}
            {latestAgentData?.follow_up_questions && latestAgentData.follow_up_questions.length > 0 && (
              <div className="space-y-1">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                  <HelpCircle className="h-3 w-3 text-blue-500" />
                  <span>Suggested Investigator Inquiries:</span>
                </div>
                <div className="flex flex-col gap-1">
                  {latestAgentData.follow_up_questions.map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSend(undefined, q)}
                      className="text-left px-2 py-1 rounded text-[11px] font-medium bg-white dark:bg-slate-900 hover:bg-blue-50 dark:hover:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200/80 dark:border-blue-900/60 transition-colors flex items-center justify-between group"
                    >
                      <span className="truncate pr-2">{q}</span>
                      <ChevronRight className="h-3 w-3 text-blue-400 opacity-60 group-hover:opacity-100 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Prompt Presets */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {promptSuggestions.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(undefined, p)}
                  className="px-2 py-0.5 rounded text-[10px] font-medium bg-white dark:bg-slate-900 hover:bg-slate-100 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 whitespace-nowrap transition-colors"
                >
                  {p.slice(0, 48)}...
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSend} className="flex gap-2">
              <Input
                placeholder={
                  selectedCaseId
                    ? `Instruct agent for case ${selectedCaseId} (e.g. identify contradictions, find legal sections)...`
                    : 'Ask an investigative query or enter case instructions...'
                }
                className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100"
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <Button
                type="submit"
                variant="primary"
                disabled={loading || !input.trim()}
                className="gap-1.5 text-xs h-9 px-3.5 bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-xs"
              >
                <Send className="h-3.5 w-3.5" />
                <span>Execute</span>
              </Button>
            </form>
          </div>
        </Card>

        {/* ==================================================================== */}
        {/* RIGHT WORKSPACE: 4 TABS (PANELS B, C, D, E) (7 COLS)                 */}
        {/* ==================================================================== */}
        <Card className="lg:col-span-7 flex flex-col h-full overflow-hidden border-slate-200/90 dark:border-slate-800 shadow-sm bg-white dark:bg-slate-900/90">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full overflow-hidden">
            {/* Tab Bar */}
            <CardHeader className="py-2 px-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 flex-shrink-0">
              <TabsList className="grid grid-cols-4 w-full bg-slate-200/70 dark:bg-slate-800/80 p-0.5">
                <TabsTrigger value="activity" className="text-[11px] gap-1.5 py-1">
                  <Activity className="h-3 w-3" />
                  <span>Agent Activity</span>
                  {latestAgentData?.tool_executions && latestAgentData.tool_executions.length > 0 && (
                    <span className="ml-1 text-[9px] px-1.5 rounded-full bg-blue-600 text-white">
                      {latestAgentData.tool_executions.length}
                    </span>
                  )}
                </TabsTrigger>

                <TabsTrigger value="findings" className="text-[11px] gap-1.5 py-1">
                  <CheckSquare className="h-3 w-3" />
                  <span>Findings & Provenance</span>
                  {latestAgentData?.factual_validation && (
                    <span className="ml-1 text-[9px] px-1.5 rounded-full bg-amber-600 text-white">
                      {latestAgentData.factual_validation.total_findings}
                    </span>
                  )}
                </TabsTrigger>

                <TabsTrigger value="research" className="text-[11px] gap-1.5 py-1">
                  <Scale className="h-3 w-3" />
                  <span>Legal & Precedents</span>
                  {latestAgentData?.legal_research?.provisions && (
                    <span className="ml-1 text-[9px] px-1.5 rounded-full bg-indigo-600 text-white">
                      {latestAgentData.legal_research.provisions.length}
                    </span>
                  )}
                </TabsTrigger>

                <TabsTrigger value="report" className="text-[11px] gap-1.5 py-1">
                  <FileText className="h-3 w-3" />
                  <span>Final Report</span>
                  {latestAgentData?.investigation_report && (
                    <span className="ml-1 text-[9px] px-1.5 rounded-full bg-emerald-600 text-white font-bold">✓</span>
                  )}
                </TabsTrigger>
              </TabsList>
            </CardHeader>

            {/* TAB 1: AGENT ACTIVITY PANEL (PANEL B) */}
            <TabsContent value="activity" className="flex-1 p-3.5 overflow-y-auto m-0 space-y-3">
              {latestAgentData ? (
                <div className="space-y-3 text-xs">
                  {/* Status Banner */}
                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">Execution Status:</span>
                        <Badge
                          variant={
                            latestAgentData.execution_status === 'completed'
                              ? 'success'
                              : latestAgentData.execution_status === 'action_blocked'
                              ? 'warning'
                              : 'destructive'
                          }
                          className="capitalize text-[10px]"
                        >
                          {latestAgentData.execution_status.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Intent classified as: <span className="font-mono font-medium text-slate-700 dark:text-slate-300">{latestAgentData.intent}</span>
                      </p>
                    </div>

                    <div className="text-right text-[11px] text-slate-500 font-mono">
                      <span>Total Tool Runtime: </span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {latestAgentData.tool_executions.reduce((acc, t) => acc + t.duration_ms, 0).toFixed(1)}ms
                      </span>
                    </div>
                  </div>

                  {/* Planned vs Executed Tools */}
                  <div className="space-y-1.5">
                    <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-500">
                      Orchestrated Tool Execution Pipeline:
                    </h3>
                    <div className="space-y-2">
                      {latestAgentData.tool_executions.map((tool, idx) => (
                        <div
                          key={idx}
                          className="border border-slate-200 dark:border-slate-800 rounded-lg p-2.5 bg-white dark:bg-slate-950/80 shadow-2xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-bold">
                                Step {idx + 1}
                              </span>
                              <span className="font-semibold text-slate-900 dark:text-slate-100">
                                {tool.tool_display_name}
                              </span>
                              <span className="text-[10px] font-mono text-slate-400">({tool.tool_name})</span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono text-slate-500">{tool.duration_ms}ms</span>
                              <Badge
                                variant={tool.status === 'success' ? 'outline' : 'destructive'}
                                className={`text-[10px] ${
                                  tool.status === 'success'
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : 'bg-red-50 text-red-700'
                                }`}
                              >
                                {tool.status}
                              </Badge>
                            </div>
                          </div>

                          <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-normal">
                            {tool.output_summary}
                          </p>

                          {/* Expandable tool arguments */}
                          <div>
                            <button
                              type="button"
                              onClick={() => setExpandedToolIndex(expandedToolIndex === idx ? null : idx)}
                              className="text-[10px] font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                            >
                              <span>{expandedToolIndex === idx ? 'Hide Payload' : 'Inspect Input Arguments'}</span>
                              <ChevronRight
                                className={`h-2.5 w-2.5 transition-transform ${
                                  expandedToolIndex === idx ? 'rotate-90' : ''
                                }`}
                              />
                            </button>
                            {expandedToolIndex === idx && (
                              <pre className="mt-1 p-2 rounded bg-slate-100 dark:bg-slate-900 font-mono text-[10px] text-slate-700 dark:text-slate-300 overflow-x-auto">
                                {JSON.stringify(tool.input_arguments, null, 2)}
                              </pre>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20 text-slate-400 gap-2">
                  <Activity className="h-8 w-8 text-slate-300 dark:text-slate-700" />
                  <p className="font-medium text-xs">No active agent run recorded yet.</p>
                  <p className="text-[11px] max-w-sm text-slate-500">
                    Submit an investigative request from the left panel. The agent will plan and execute tools with full telemetry.
                  </p>
                </div>
              )}
            </TabsContent>

            {/* TAB 2: INVESTIGATION FINDINGS PANEL (PANEL C) */}
            <TabsContent value="findings" className="flex-1 p-3.5 overflow-y-auto m-0 space-y-3.5 text-xs">
              {latestAgentData?.complaint_analysis || latestAgentData?.factual_validation ? (
                <div className="space-y-3.5">
                  {/* Extracted Facts Overview */}
                  {latestAgentData.complaint_analysis && (
                    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-950 space-y-2.5">
                      <div className="flex items-center justify-between border-b pb-2 border-slate-100 dark:border-slate-800">
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                          <CheckSquare className="h-4 w-4 text-blue-500" />
                          <span>Extracted Case Facts & Parties</span>
                        </h3>
                        <Badge variant="outline" className="font-mono text-[10px]">
                          Docket: {latestAgentData.complaint_analysis.reference_id}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                          <span className="text-slate-400 font-medium">Complainant:</span>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">
                            {latestAgentData.complaint_analysis.complainant || 'Not identified in text'}
                          </div>
                        </div>

                        <div className="p-2 rounded bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                          <span className="text-slate-400 font-medium">Reported Accused / Suspects:</span>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">
                            {latestAgentData.complaint_analysis.accused_parties.length > 0
                              ? latestAgentData.complaint_analysis.accused_parties.join(', ')
                              : 'Unidentified'}
                          </div>
                        </div>

                        <div className="p-2 rounded bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                          <span className="text-slate-400 font-medium">Incident Date & Time:</span>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">
                            {latestAgentData.complaint_analysis.incident_date || 'Unspecified Date'} |{' '}
                            {latestAgentData.complaint_analysis.incident_time || 'Unspecified Time'}
                          </div>
                        </div>

                        <div className="p-2 rounded bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                          <span className="text-slate-400 font-medium">Place of Occurrence:</span>
                          <div className="font-semibold text-slate-800 dark:text-slate-200">
                            {latestAgentData.complaint_analysis.incident_location || 'Unspecified'}
                          </div>
                        </div>
                      </div>

                      {/* Established Facts vs Allegations */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                        <div className="space-y-1">
                          <h4 className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" /> Established Source Facts:
                          </h4>
                          <ul className="space-y-1">
                            {latestAgentData.complaint_analysis.established_facts.map((f, i) => (
                              <li key={i} className="text-[11px] text-slate-700 dark:text-slate-300 bg-emerald-50/50 dark:bg-emerald-950/20 p-1.5 rounded border border-emerald-100 dark:border-emerald-900/40">
                                {f}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="space-y-1">
                          <h4 className="text-[10px] font-bold text-amber-600 uppercase tracking-wider flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" /> Unsubstantiated Allegations:
                          </h4>
                          <ul className="space-y-1">
                            {latestAgentData.complaint_analysis.allegations.length > 0 ? (
                              latestAgentData.complaint_analysis.allegations.map((a, i) => (
                                <li key={i} className="text-[11px] text-slate-700 dark:text-slate-300 bg-amber-50/50 dark:bg-amber-950/20 p-1.5 rounded border border-amber-100 dark:border-amber-900/40">
                                  {a}
                                </li>
                              ))
                            ) : (
                              <li className="text-[11px] text-slate-400 italic">No disputed allegations reported</li>
                            )}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Evidence Provenance Matrix */}
                  {latestAgentData.evidence_provenance && (
                    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-950 space-y-2">
                      <div className="flex items-center justify-between border-b pb-2 border-slate-100 dark:border-slate-800">
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                          <ShieldCheck className="h-4 w-4 text-emerald-500" />
                          <span>Evidence Provenance & Character-Level Invariant</span>
                        </h3>
                        <Badge
                          variant="outline"
                          className={
                            latestAgentData.evidence_provenance.provenance_invariant_preserved
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200 font-mono text-[10px]'
                              : 'bg-red-50 text-red-700 font-mono text-[10px]'
                          }
                        >
                          {latestAgentData.evidence_provenance.provenance_invariant_preserved
                            ? '✅ Provenance Invariant Preserved'
                            : '❌ Mismatches Detected'}
                        </Badge>
                      </div>

                      <p className="text-[11px] text-slate-500 font-mono">
                        Invariant verification check: raw_text[start_offset:end_offset] == span_text. Verified:{' '}
                        {latestAgentData.evidence_provenance.verified_count}/
                        {latestAgentData.evidence_provenance.total_facts_checked}
                      </p>

                      <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                        {latestAgentData.evidence_provenance.spans.map((sp, idx) => (
                          <div
                            key={idx}
                            className="p-2 rounded bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]"
                          >
                            <div>
                              <span className="font-mono font-semibold text-blue-600 dark:text-blue-400 mr-2">
                                [{sp.fact_type}]
                              </span>
                              <span className="font-medium text-slate-800 dark:text-slate-200">
                                "{sp.original_text}"
                              </span>
                            </div>
                            <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400">
                              <span>
                                Offset: [{sp.start_offset}:{sp.end_offset}]
                              </span>
                              <Badge variant="outline" className="text-[9px] bg-emerald-50 text-emerald-700">
                                Verified
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Contradiction & Validation Alerts */}
                  {latestAgentData.factual_validation && latestAgentData.factual_validation.all_findings.length > 0 && (
                    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-950 space-y-2">
                      <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 border-b pb-2 border-slate-100 dark:border-slate-800">
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                        <span>Factual Inconsistencies & Statutory Omissions</span>
                      </h3>

                      <div className="space-y-2">
                        {latestAgentData.factual_validation.all_findings.map((finding, idx) => (
                          <div
                            key={idx}
                            className={`p-2.5 rounded-lg border text-[11px] space-y-1 ${
                              finding.category.includes('contradiction')
                                ? 'bg-red-500/10 border-red-500/30 text-red-900 dark:text-red-200'
                                : finding.category.includes('missing')
                                ? 'bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200'
                                : 'bg-blue-500/10 border-blue-500/30 text-blue-900 dark:text-blue-200'
                            }`}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span className="capitalize">{finding.category.replace('_', ' ')}</span>
                              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/60 dark:bg-black/40">
                                Severity: {finding.severity}
                              </span>
                            </div>
                            <p className="font-medium">{finding.explanation}</p>
                            {finding.suggested_action && (
                              <p className="text-[10px] text-slate-600 dark:text-slate-400">
                                <strong>Recommended Action:</strong> {finding.suggested_action}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20 text-slate-400 gap-2">
                  <CheckSquare className="h-8 w-8 text-slate-300 dark:text-slate-700" />
                  <p className="font-medium text-xs">No case findings currently loaded.</p>
                  <p className="text-[11px] max-w-sm text-slate-500">
                    Select a case docket or instruct the agent to "Analyse complaint &lt;case-id&gt;" to generate findings and evidence spans.
                  </p>
                </div>
              )}
            </TabsContent>

            {/* TAB 3: LEGAL & PRECEDENT RESEARCH PANEL (PANEL D) */}
            <TabsContent value="research" className="flex-1 p-3.5 overflow-y-auto m-0 space-y-3.5 text-xs">
              {latestAgentData?.legal_research || latestAgentData?.similar_cases ? (
                <div className="space-y-3.5">
                  {/* Verified Legal Provisions */}
                  {latestAgentData.legal_research && (
                    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-950 space-y-2.5">
                      <div className="flex items-center justify-between border-b pb-2 border-slate-100 dark:border-slate-800">
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                          <Scale className="h-4 w-4 text-indigo-500" />
                          <span>Applicable Bharatiya Nyaya Sanhita (BNS 2023) Sections</span>
                        </h3>
                        <Badge variant="outline" className="text-[10px] bg-indigo-50 text-indigo-700 border-indigo-200">
                          {latestAgentData.legal_research.provisions.length} Grounded Provisions
                        </Badge>
                      </div>

                      <p className="text-[10px] text-slate-500 italic">
                        {latestAgentData.legal_research.statutory_notes}
                      </p>

                      <div className="space-y-2.5">
                        {latestAgentData.legal_research.provisions.map((prov, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 space-y-1.5"
                          >
                            <div className="flex items-center justify-between flex-wrap gap-1">
                              <h4 className="font-bold text-xs text-slate-900 dark:text-white">{prov.title}</h4>
                              <div className="flex items-center gap-1.5">
                                {prov.cognizable !== null && (
                                  <Badge
                                    variant="outline"
                                    className={`text-[9px] ${
                                      prov.cognizable
                                        ? 'bg-red-50 text-red-700 border-red-200'
                                        : 'bg-emerald-50 text-emerald-700'
                                    }`}
                                  >
                                    {prov.cognizable ? 'Cognizable' : 'Non-Cognizable'}
                                  </Badge>
                                )}
                                {prov.bailable !== null && (
                                  <Badge
                                    variant="outline"
                                    className={`text-[9px] ${
                                      prov.bailable ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'
                                    }`}
                                  >
                                    {prov.bailable ? 'Bailable' : 'Non-Bailable'}
                                  </Badge>
                                )}
                              </div>
                            </div>

                            <p className="text-[11px] text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                              {prov.content}
                            </p>

                            <div className="text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                              <span>Source: {prov.source}</span>
                              {prov.ipc_counterpart && <span>Counterpart: {prov.ipc_counterpart}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Similar Precedent Cases from FAISS */}
                  {latestAgentData.similar_cases && (
                    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-3 bg-white dark:bg-slate-950 space-y-2.5">
                      <div className="flex items-center justify-between border-b pb-2 border-slate-100 dark:border-slate-800">
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                          <BookOpen className="h-4 w-4 text-blue-500" />
                          <span>Precedent Modus Operandi & Similar Cases (FAISS)</span>
                        </h3>
                        <Badge variant="outline" className="text-[10px]">
                          {latestAgentData.similar_cases.cases.length} Matches
                        </Badge>
                      </div>

                      <Alert className="py-2 px-3 bg-blue-500/10 border-blue-500/20 text-blue-800 dark:text-blue-300 text-[10px]">
                        <AlertCircle className="h-3.5 w-3.5 text-blue-500" />
                        <AlertDescription className="ml-1 leading-normal">
                          {latestAgentData.similar_cases.disclaimer}
                        </AlertDescription>
                      </Alert>

                      <div className="space-y-2">
                        {latestAgentData.similar_cases.cases.map((sc, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                                Docket {sc.reference_id}
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                                Match Score: {(sc.score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-700 dark:text-slate-300">{sc.summary}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20 text-slate-400 gap-2">
                  <Scale className="h-8 w-8 text-slate-300 dark:text-slate-700" />
                  <p className="font-medium text-xs">No statutory or case precedent research loaded.</p>
                  <p className="text-[11px] max-w-sm text-slate-500">
                    Ask legal questions like "Which section applies to house trespass?" or run a full investigation workflow.
                  </p>
                </div>
              )}
            </TabsContent>

            {/* TAB 4: FINAL REPORT PANEL (PANEL E) */}
            <TabsContent value="report" className="flex-1 p-3.5 overflow-y-auto m-0 space-y-3.5 text-xs">
              {latestAgentData?.investigation_report ? (
                <div className="space-y-3.5">
                  {/* Actions Bar */}
                  <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                    <div>
                      <h3 className="font-bold text-slate-900 dark:text-slate-100 text-xs">
                        {latestAgentData.investigation_report.title}
                      </h3>
                      <p className="text-[10px] text-slate-500">
                        Generated on {latestAgentData.investigation_report.generated_at}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCopyReport}
                        className="h-7 text-xs gap-1 text-slate-600 hover:text-slate-900"
                      >
                        <Copy className="h-3 w-3" />
                        <span>Copy Markdown</span>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownloadReport}
                        className="h-7 text-xs gap-1 text-blue-600 hover:text-blue-700"
                      >
                        <Download className="h-3 w-3" />
                        <span>Download (.md)</span>
                      </Button>
                    </div>
                  </div>

                  {/* Human In The Loop Notice */}
                  <Alert className="py-2.5 px-3 bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200">
                    <ShieldAlert className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-[11px] leading-relaxed ml-1.5">
                      <strong>Human-in-the-Loop Safeguard:</strong> {latestAgentData.investigation_report.human_review_notice}
                    </AlertDescription>
                  </Alert>

                  {/* Formatted Report Preview */}
                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-2xs font-sans text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {latestAgentData.investigation_report.formatted_markdown}
                  </div>

                  {/* Verification & Human Approval Box */}
                  <div className="p-3 rounded-lg border border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/50 dark:bg-emerald-950/20 flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Investigator Concurrence Required</span>
                      </h4>
                      <p className="text-[11px] text-emerald-700 dark:text-emerald-400 mt-0.5">
                        Verify facts and legal sections against primary complaint before advancing to formal FIR generation.
                      </p>
                    </div>

                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => toast.success('Findings verified and approved by Investigating Officer.')}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-8 px-3"
                    >
                      <Check className="h-3.5 w-3.5 mr-1" />
                      Approve Findings
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20 text-slate-400 gap-2">
                  <FileText className="h-8 w-8 text-slate-300 dark:text-slate-700" />
                  <p className="font-medium text-xs">No Investigation Report has been generated yet.</p>
                  <p className="text-[11px] max-w-sm text-slate-500">
                    Instruct the agent: "Analyse complaint &lt;case-id&gt; and prepare an investigation summary."
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </Card>
      </div>
    </div>
  )
}
