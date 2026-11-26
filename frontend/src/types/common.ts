// types/common.ts
export interface ApiError {
  detail: string
  status?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface DashboardStats {
  total_complaints: number
  drafts_generated: number
  awaiting_review: number
  reviewed: number
  complaints_over_time: { date: string; count: number }[]
  status_distribution: { status: string; count: number }[]
  category_distribution: { category: string; count: number }[]
  severity_distribution: { severity: string; count: number }[]
}

export interface SimilarCase {
  id: string
  reference_id: string
  title: string
  similarity_score: number
  summary?: string
  category?: string
  status: string
}

export interface LegalDocument {
  id: string
  title: string
  source: string
  content: string
  relevance_score: number
  provisions?: string[]
}

export interface AssistantMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  citations?: Citation[]
}

export interface Citation {
  id: string
  title: string
  source: string
  snippet: string
  relevance_score: number
}

export interface AIModel {
  id: string
  name: string
  model_type: 'ner' | 'generation' | 'validation' | 'similarity' | 'retrieval'
  status: 'loaded' | 'not_loaded' | 'error'
  checkpoint_path?: string
  is_pretrained: boolean
  description?: string
  last_evaluated?: string
  metrics?: Record<string, number>
}

export interface EvaluationResult {
  system: string
  metrics: Record<string, Record<string, number>>
  evaluated_at: string
}

export interface ReviewWorkflow {
  complaint_id: string
  reviewer_id?: string
  reviewer_name?: string
  assigned_at?: string
  reviewed_at?: string
  status: 'pending' | 'in_review' | 'completed' | 'rejected'
  notes?: string
  final_action?: 'approved' | 'rejected' | 'revision_required'
}
