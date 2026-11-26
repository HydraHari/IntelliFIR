// api/legal.ts
import apiClient from './client'

export interface LegalSearchResult {
  id: string
  title: string
  source: string
  provision_type: string
  snippet: string
  score: number
}

export interface LegalDocument {
  id: string
  title: string
  source: string
  version?: string
  provision_type: string
  created_at: string
}

export const legalApi = {
  search: (query: string, top_k: number = 5) =>
    apiClient
      .post<LegalSearchResult[]>('/legal/search', { query, top_k })
      .then((r) => r.data),

  listDocuments: () =>
    apiClient.get<LegalDocument[]>('/legal/documents').then((r) => r.data),

  addDocument: (data: {
    title: string
    source: string
    content: string
    provision_type?: string
    version?: string
  }) => apiClient.post('/legal/documents', data).then((r) => r.data),
}
