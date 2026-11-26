// api/validation.ts
import apiClient from './client'
import type { UpdateFindingRequest, ValidationReport } from '../types/validation'

export const validationApi = {
  getForDraft: (draftId: string) =>
    apiClient.get<ValidationReport>(`/drafts/${draftId}/validation`).then((r) => r.data),

  trigger: (draftId: string) =>
    apiClient.post<ValidationReport>(`/drafts/${draftId}/validate`).then((r) => r.data),

  updateFinding: (findingId: string, data: UpdateFindingRequest) =>
    apiClient.put(`/findings/${findingId}/decision`, data).then((r) => r.data),
}
