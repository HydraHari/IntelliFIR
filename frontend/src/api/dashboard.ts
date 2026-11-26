// api/dashboard.ts
import apiClient from './client'

export interface DashboardStats {
  total_complaints: number
  complaints_by_status: Array<{ status: string; count: number }>
  total_drafts: number
  total_findings: number
  pending_reviews: number
  recent_activity: Array<{
    id: string
    action: string
    resource_type: string
    resource_id?: string
    created_at: string
  }>
}

export const dashboardApi = {
  getStats: () => apiClient.get<DashboardStats>('/dashboard/stats').then((r) => r.data),
}
