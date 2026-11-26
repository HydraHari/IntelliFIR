import React, { useEffect, useState } from 'react'
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Play,
  RefreshCw,
  Layers,
  ShieldCheck,
  Database,
  Sliders,
  Terminal,
  Activity,
  Zap,
} from 'lucide-react'
import { modelsApi, type ModelStatusInfo } from '../api/models'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { LoadingSpinner } from '../components/common/UIStates'

export const ModelsPage: React.FC = () => {
  const [models, setModels] = useState<ModelStatusInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    setLoading(true)
    try {
      const data = await modelsApi.list()
      setModels(data || [])
    } catch (err) {
      console.error('Failed to load AI models:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadNer = async () => {
    setActionLoading(true)
    setMessage(null)
    try {
      const resp = await modelsApi.loadNer()
      setMessage(resp.message)
      await loadModels()
    } catch (err: any) {
      setMessage(`Error loading model checkpoint: ${err?.response?.data?.detail || err.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Querying neural network checkpoint statuses..." />
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-1 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              AI Model Engine & Inference Status
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              Hardware & ML Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time status of loaded token classification checkpoints, vector sentence encoders, and RAG reasoning providers.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadModels}
          className="h-8 gap-1.5 text-xs border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Checkpoints</span>
        </Button>
      </div>

      {message && (
        <div className="p-3 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-300 rounded-lg text-xs font-medium flex items-center gap-2">
          <Activity className="h-4 w-4" />
          <span>{message}</span>
        </div>
      )}

      {/* Model Cards */}
      <div className="space-y-3.5">
        {models.map((m) => {
          const isLoaded = m.status === 'loaded' || m.status === 'active'
          return (
            <Card
              key={m.id}
              className="border-slate-200/90 dark:border-slate-800 shadow-2xs overflow-hidden bg-white dark:bg-slate-900/90"
            >
              <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-50/70 dark:bg-slate-950/50">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold shadow-2xs">
                    <Cpu className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                      {m.name}
                    </h3>
                    <p className="text-[11px] text-slate-400">{m.model_type}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {m.is_finetuned ? (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 font-medium">
                      Fine-Tuned Checkpoint
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 font-medium">
                      Pretrained Baseline
                    </span>
                  )}

                  <span
                    className={`inline-flex items-center gap-1.5 text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full border ${
                      isLoaded
                        ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                        : 'bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800'
                    }`}
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        isLoaded ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                    />
                    {m.status}
                  </span>
                </div>
              </div>

              <CardContent className="p-5 space-y-3.5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                      Checkpoint / Weights Identifier
                    </span>
                    <span className="font-mono text-xs text-slate-800 dark:text-slate-200 block mt-1 break-all bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                      {m.checkpoint_location}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                      Runtime Execution Backend
                    </span>
                    <span className="text-xs text-slate-800 dark:text-slate-200 block mt-1 bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                      {m.id === 'ner_model'
                        ? 'PyTorch / HuggingFace Transformers Token Classification'
                        : m.id === 'embedding_model'
                        ? 'Sentence-Transformers / FAISS Dense Vector C++'
                        : 'Local Ollama Container / Deterministic Fallback'}
                    </span>
                  </div>
                </div>

                {m.evaluation_metrics && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400 block tracking-wider mb-2">
                      Held-Out Validation Benchmark (Empirical Score)
                    </span>
                    <div className="grid grid-cols-3 gap-2 text-center font-mono">
                      <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span className="text-[9px] text-slate-400 uppercase block">Precision</span>
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                          {(m.evaluation_metrics.precision * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span className="text-[9px] text-slate-400 uppercase block">Recall</span>
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                          {(m.evaluation_metrics.recall * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span className="text-[9px] text-slate-400 uppercase block">F1 Score</span>
                        <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                          {(m.evaluation_metrics.f1 * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {m.id === 'ner_model' && !isLoaded && (
                  <div className="pt-1">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleLoadNer}
                      disabled={actionLoading}
                      className="h-8 gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium"
                    >
                      <Play className="h-3 w-3" />
                      <span>{actionLoading ? 'Allocating Tensors...' : 'Initialize Model Checkpoint'}</span>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
