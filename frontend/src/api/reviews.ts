// api/reviews.ts
import apiClient from './client'

export interface ReviewRecord {
  id: string
  draft_id: string
  reviewer_id: string
  action: string
  notes?: string
  created_at: string
}

export const reviewsApi = {
  record: (draftId: string, action: string, notes?: string) =>
    apiClient
      .post<ReviewRecord>(`/drafts/${draftId}/review`, { action, notes })
      .then((r) => r.data),

  list: () =>
    apiClient.get<{ items: ReviewRecord[]; total: number }>('/reviews').then((r) => r.data),
}
