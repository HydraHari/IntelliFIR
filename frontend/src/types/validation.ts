// types/validation.ts
export type ValidationCategory =
  | 'factual_support'
  | 'missing_information'
  | 'ambiguity'
  | 'contradiction'
  | 'unsupported_claim'

export type Severity = 'low' | 'medium' | 'high'

export type ReviewerAction = 'accepted' | 'rejected' | 'needs_clarification' | 'clarification_requested' | 'pending'

export interface ValidationFinding {
  id: string
  category: ValidationCategory
  severity: Severity
  draft_claim: string
  source_evidence?: string
  explanation: string
  suggested_action?: string
  reviewer_action?: ReviewerAction
  reviewer_notes?: string
}

export interface ValidationReport {
  id: string
  complaint_id: string
  draft_id: string
  findings: ValidationFinding[]
  supported_count: number
  unsupported_count: number
  missing_count: number
  ambiguous_count: number
  contradiction_count: number
  generated_at: string
  overall_confidence: number
}

export interface UpdateFindingRequest {
  reviewer_action: ReviewerAction
  reviewer_notes?: string
}
