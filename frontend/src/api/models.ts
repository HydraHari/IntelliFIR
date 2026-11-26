// api/models.ts
import apiClient from './client'

export interface ModelStatusInfo {
  id: string
  name: string
  model_type: string
  checkpoint_location: string
  status: string
  is_finetuned: boolean
  evaluation_metrics?: Record<string, any>
}

export const modelsApi = {
  list: () => apiClient.get<ModelStatusInfo[]>('/models').then((r) => r.data),
  loadNer: () => apiClient.post('/models/load-ner').then((r) => r.data),
}
