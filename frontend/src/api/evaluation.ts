// api/evaluation.ts
import apiClient from './client'

export interface EvaluationResults {
  status: string
  message?: string
  dataset_path?: string
  sample_count?: number
  results?: {
    Baseline_A_Direct_LLM: Record<string, any>
    Baseline_B_Template: Record<string, any>
    IntelliFIR_Proposed: Record<string, any>
  }
}

export const evaluationApi = {
  getResults: () => apiClient.get<EvaluationResults>('/evaluation/results').then((r) => r.data),
  run: () => apiClient.post<EvaluationResults>('/evaluation/run').then((r) => r.data),
}
