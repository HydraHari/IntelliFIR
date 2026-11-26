// api/complaints.ts
import apiClient from './client'
import type {
  Complaint,
  ComplaintListResponse,
  CreateComplaintRequest,
} from '../types/complaint'

export interface ComplaintFilters {
  skip?: number
  limit?: number
  status?: string
  search?: string
}

export const complaintsApi = {
  list: (filters: ComplaintFilters = {}) =>
    apiClient.get<ComplaintListResponse>('/complaints', { params: filters }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Complaint>(`/complaints/${id}`).then((r) => r.data),

  create: (data: CreateComplaintRequest) =>
    apiClient.post<Complaint>('/complaints', data).then((r) => r.data),

  upload: (data: FormData) =>
    apiClient
      .post<Complaint>('/complaints/upload', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/complaints/${id}`).then((r) => r.data),

  generateDraft: (id: string, method: string = 'template') =>
    apiClient.post(`/complaints/${id}/generate-draft`, { method }).then((r) => r.data),

  process: (id: string) =>
    apiClient.post(`/complaints/${id}/process`).then((r) => r.data),

  getExtraction: (id: string) =>
    apiClient.get(`/complaints/${id}/extraction`).then((r) => r.data),
}
