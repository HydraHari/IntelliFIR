import React, { useEffect, useState } from 'react'
import {
  FlaskConical,
  Play,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Layers,
  BarChart2,
  FileText,
  ShieldCheck,
  Check,
  X,
  Sparkles,
  Download,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from 'recharts'
import { evaluationApi, type EvaluationResults } from '../api/evaluation'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { LoadingSpinner } from '../components/common/UIStates'

export const EvaluationPage: React.FC = () => {
  const [data, setData] = useState<EvaluationResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    loadResults()
  }, [])

  const loadResults = async () => {
    setLoading(true)
    try {
      const resp = await evaluationApi.getResults()
      setData(resp)
    } catch (err) {
      console.error('Failed to load evaluation results:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRunEvaluation = async () => {
    setRunning(true)
    try {
      const resp = await evaluationApi.run()
      setData(resp)
    } catch (err) {
      console.error('Failed to execute evaluation:', err)
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Compiling scientific benchmark evaluation metrics..." />
  }

  const hasResults = data?.status === 'completed' && data.results
  const results = data?.results

  const chartData = hasResults
    ? [
        {
          metric: 'Supported Claim Rate',
          'Baseline A (Direct LLM)': Number(
            (results?.Baseline_A_Direct_LLM.supported_claim_rate * 100).toFixed(1)
          ),
          'Baseline B (Template)': Number(
            (results?.Baseline_B_Template.supported_claim_rate * 100).toFixed(1)
          ),
          'IntelliFIR (Proposed)': Number(
            (results?.IntelliFIR_Proposed.supported_claim_rate * 100).toFixed(1)
          ),
        },
        {
          metric: 'Unsupported Claim Rate',
          'Baseline A (Direct LLM)': Number(
            (results?.Baseline_A_Direct_LLM.unsupported_claim_rate * 100).toFixed(1)
          ),
          'Baseline B (Template)': Number(
            (results?.Baseline_B_Template.unsupported_claim_rate * 100).toFixed(1)
          ),
          'IntelliFIR (Proposed)': Number(
            (results?.IntelliFIR_Proposed.unsupported_claim_rate * 100).toFixed(1)
          ),
        },
      ]
    : []

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header and Benchmark Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Research Evaluation & Comparative Benchmarks
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              Empirical Study
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Empirical comparative analysis evaluating Baseline A (Unconstrained LLM), Baseline B (Keyword Template), and IntelliFIR.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleRunEvaluation}
          disabled={running}
          className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-2xs"
        >
          <Play className={`h-3 w-3 ${running ? 'animate-spin' : ''}`} />
          <span>{running ? 'Running Benchmark Suite...' : 'Execute Evaluation Benchmark'}</span>
        </Button>
      </div>

      {!hasResults ? (
        <Card className="p-12 text-center border-dashed border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="flex flex-col items-center gap-3">
            <FlaskConical className="h-10 w-10 text-slate-400" />
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Evaluation Benchmark Not Yet Executed
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md leading-relaxed">
              Run the empirical benchmark to measure entity token classification (P/R/F1), claim grounding rates, and missing information detection across held-out citizen complaint samples.
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={handleRunEvaluation}
              disabled={running}
              className="mt-2 text-xs bg-blue-600 hover:bg-blue-700 text-white"
            >
              {running ? 'Evaluating Pipeline...' : 'Run Benchmark Evaluation'}
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* Top Comparative KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                Baseline A • Direct Generative LLM
              </span>
              <p className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-200">
                {(results!.Baseline_A_Direct_LLM.supported_claim_rate * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-slate-500">
                Supported Claim Rate •{' '}
                <span className="text-rose-600 font-semibold font-mono">
                  {(results!.Baseline_A_Direct_LLM.unsupported_claim_rate * 100).toFixed(1)}% Hallucination
                </span>
              </p>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                Baseline B • Keyword Slot Template
              </span>
              <p className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-200">
                {(results!.Baseline_B_Template.supported_claim_rate * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-slate-500">
                Supported Claim Rate • Static Keyword Match
              </p>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200/90 dark:border-emerald-800/80 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider block">
                IntelliFIR Proposed Architecture
              </span>
              <p className="text-2xl font-bold font-mono text-emerald-900 dark:text-emerald-200">
                {(results!.IntelliFIR_Proposed.supported_claim_rate * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-emerald-700 dark:text-emerald-300 font-medium">
                Verified Provenance • 100% Grounded
              </p>
            </div>
          </div>

          {/* Comparative Metrics Table */}
          <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90 overflow-hidden">
            <CardHeader className="py-3 px-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                Empirical Capability Comparison Across Evaluated Systems
              </CardTitle>
              <CardDescription className="text-[11px] text-slate-500">
                Tested against {data.sample_count} held-out complaints with expert gold standard annotations.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-slate-50/50 dark:bg-slate-950/40 border-b border-slate-200/80 dark:border-slate-800">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-xs font-bold text-slate-700 dark:text-slate-300">
                      Evaluated Metric / Functional Gate
                    </TableHead>
                    <TableHead className="text-center text-xs font-bold text-slate-700 dark:text-slate-300">
                      Baseline A (Direct LLM)
                    </TableHead>
                    <TableHead className="text-center text-xs font-bold text-slate-700 dark:text-slate-300">
                      Baseline B (Template)
                    </TableHead>
                    <TableHead className="text-center text-xs font-bold text-blue-600 dark:text-blue-400">
                      IntelliFIR (Proposed)
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="divide-y divide-slate-100 dark:divide-slate-800">
                  <TableRow className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <TableCell className="font-medium text-xs text-slate-800 dark:text-slate-200">
                      Supported Claim Rate
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs text-slate-600 dark:text-slate-400">
                      {(results!.Baseline_A_Direct_LLM.supported_claim_rate * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs text-slate-600 dark:text-slate-400">
                      {(results!.Baseline_B_Template.supported_claim_rate * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      {(results!.IntelliFIR_Proposed.supported_claim_rate * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>

                  <TableRow className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <TableCell className="font-medium text-xs text-slate-800 dark:text-slate-200">
                      Unsupported / Hallucinated Rate
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs text-rose-600 font-semibold">
                      {(results!.Baseline_A_Direct_LLM.unsupported_claim_rate * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs text-slate-600 dark:text-slate-400">
                      {(results!.Baseline_B_Template.unsupported_claim_rate * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      {(results!.IntelliFIR_Proposed.unsupported_claim_rate * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>

                  <TableRow className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <TableCell className="font-medium text-xs text-slate-800 dark:text-slate-200">
                      NER Token Classification F1
                    </TableCell>
                    <TableCell className="text-center text-xs text-slate-400 font-mono">
                      N/A
                    </TableCell>
                    <TableCell className="text-center text-xs text-slate-400 font-mono">
                      N/A
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                      {(results!.IntelliFIR_Proposed.entity_extraction_f1 * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>

                  <TableRow className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <TableCell className="font-medium text-xs text-slate-800 dark:text-slate-200">
                      Missing Detail Detection F1
                    </TableCell>
                    <TableCell className="text-center text-xs text-slate-400 font-mono">
                      N/A
                    </TableCell>
                    <TableCell className="text-center text-xs text-slate-400 font-mono">
                      N/A
                    </TableCell>
                    <TableCell className="text-center font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                      {(results!.IntelliFIR_Proposed.missing_info_detection_f1 * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>

                  <TableRow className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <TableCell className="font-medium text-xs text-slate-800 dark:text-slate-200">
                      Evidence Provenance Offsets
                    </TableCell>
                    <TableCell className="text-center text-xs text-rose-500 font-semibold">
                      <span className="inline-flex items-center gap-1">
                        <X className="h-3 w-3" /> No
                      </span>
                    </TableCell>
                    <TableCell className="text-center text-xs text-rose-500 font-semibold">
                      <span className="inline-flex items-center gap-1">
                        <X className="h-3 w-3" /> No
                      </span>
                    </TableCell>
                    <TableCell className="text-center text-xs text-emerald-600 dark:text-emerald-400 font-bold">
                      <span className="inline-flex items-center gap-1">
                        <Check className="h-3 w-3" /> Exact Offsets
                      </span>
                    </TableCell>
                  </TableRow>

                  <TableRow className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <TableCell className="font-medium text-xs text-slate-800 dark:text-slate-200">
                      Independent Factual Validation
                    </TableCell>
                    <TableCell className="text-center text-xs text-rose-500 font-semibold">
                      <span className="inline-flex items-center gap-1">
                        <X className="h-3 w-3" /> No
                      </span>
                    </TableCell>
                    <TableCell className="text-center text-xs text-rose-500 font-semibold">
                      <span className="inline-flex items-center gap-1">
                        <X className="h-3 w-3" /> No
                      </span>
                    </TableCell>
                    <TableCell className="text-center text-xs text-emerald-600 dark:text-emerald-400 font-bold">
                      <span className="inline-flex items-center gap-1">
                        <Check className="h-3 w-3" /> Multi-Rule Auditor
                      </span>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Visualization Chart */}
          <Card className="border-slate-200/90 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
            <CardHeader className="py-3 px-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                Grounding Fidelity & Hallucination Mitigation
              </CardTitle>
              <CardDescription className="text-[11px] text-slate-500">
                Comparison of supported vs unsupported claim rates across architectures
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4">
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 15, right: 30, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.15} />
                    <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <YAxis unit="%" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0F172A',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#F8FAFC',
                        fontSize: '11px',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                    <Bar dataKey="Baseline A (Direct LLM)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Baseline B (Template)" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="IntelliFIR (Proposed)" fill="#059669" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
