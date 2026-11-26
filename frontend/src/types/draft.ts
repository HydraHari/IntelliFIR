// types/draft.ts
export type DraftStatus = 'draft' | 'finalized' | 'rejected'

export interface FIRDraft {
  id: string
  complaint_id: string
  content: string
  version: number
  status: DraftStatus
  generated_at: string
  updated_at: string
  generated_by?: string
  model_used?: string
}

export interface UpdateDraftRequest {
  content: string
}
