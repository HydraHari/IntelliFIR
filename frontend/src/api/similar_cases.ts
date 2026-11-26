// api/similar_cases.ts
import apiClient from './client'

export interface SimilarCase {
  id: string
  reference_id: string
  summary: string
  category?: string
  score: number
  metadata?: Record<string, any>
}

export interface SimilarCaseSearchResponse {
  query: string
  results: SimilarCase[]
  total_found: number
}

export const similarCasesApi = {
  search: (query: string, top_k: number = 5, threshold?: number) =>
    apiClient
      .post<SimilarCaseSearchResponse>('/similar-cases/search', {
        query,
        top_k,
        threshold,
      })
      .then((r) => r.data),

  ingest: (data: { reference_id: string; summary: string; category?: string; metadata?: any }) =>
    apiClient.post('/similar-cases/ingest', data).then((r) => r.data),
}
