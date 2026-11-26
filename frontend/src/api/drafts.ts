// api/drafts.ts
import apiClient from './client'
import type { FIRDraft, UpdateDraftRequest } from '../types/draft'

export const draftsApi = {
  getForComplaint: (complaintId: string) =>
    apiClient.get<FIRDraft>(`/complaints/${complaintId}/draft`).then((r) => r.data),

  generate: (complaintId: string, method: string = 'template') =>
    apiClient
      .post<FIRDraft>(`/complaints/${complaintId}/generate-draft`, { method })
      .then((r) => r.data),

  update: (draftId: string, data: UpdateDraftRequest) =>
    apiClient.put<FIRDraft>(`/drafts/${draftId}`, data).then((r) => r.data),

  exportDocxUrl: (draftId: string) =>
    `${apiClient.defaults.baseURL}/drafts/${draftId}/export/docx`,
}
