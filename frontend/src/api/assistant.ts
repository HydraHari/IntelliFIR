// api/assistant.ts
import apiClient from './client'

export interface AssistantQueryRequest {
  question: string
  complaint_id?: string
}

export interface AssistantQueryResponse {
  answer: string
  sources: Array<{
    title: string
    content: string
    score?: number
  }>
  citations: string[]
  is_retrieval_only: boolean
}

export const assistantApi = {
  query: (data: AssistantQueryRequest) =>
    apiClient.post<AssistantQueryResponse>('/assistant/query', data).then((r) => r.data),
}
