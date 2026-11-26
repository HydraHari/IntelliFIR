// api/assistant.ts
import apiClient from './client'

export interface ToolExecutionRecord {
  tool_name: string
  tool_display_name: string
  input_arguments: Record<string, any>
  output_summary: string
  status: 'success' | 'failed' | 'skipped'
  duration_ms: number
  error?: string | null
  timestamp: string
}

export interface ComplaintAnalysisOutput {
  complaint_id: string
  reference_id: string
  title: string
  language: string
  raw_text: string
  complainant?: string | null
  accused_parties: string[]
  victims: string[]
  witnesses: string[]
  incident_date?: string | null
  incident_time?: string | null
  incident_location?: string | null
  property_involved: string[]
  amount_involved?: string | null
  weapons_used: string[]
  established_facts: string[]
  allegations: string[]
  uncertain_details: string[]
  missing_details: string[]
  total_facts_extracted: number
}

export interface EvidenceSpanItem {
  fact_type: string
  fact_value: string
  start_offset: number
  end_offset: number
  original_text: string
  verified: boolean
  source_sentence?: string | null
  error_reason?: string | null
}

export interface EvidenceProvenanceOutput {
  total_facts_checked: number
  verified_count: number
  unsupported_count: number
  spans: EvidenceSpanItem[]
  unsupported_facts: string[]
  provenance_invariant_preserved: boolean
}

export interface ValidationFindingItem {
  finding_id: string
  category: string
  claim_or_statement: string
  explanation: string
  severity: string
  suggested_action: string
  source_evidence?: string | null
}

export interface FactualValidationOutput {
  total_findings: number
  contradictions: ValidationFindingItem[]
  timeline_inconsistencies: ValidationFindingItem[]
  missing_statutory_elements: ValidationFindingItem[]
  ambiguities: ValidationFindingItem[]
  unsupported_claims: ValidationFindingItem[]
  all_findings: ValidationFindingItem[]
}

export interface LegalProvisionItem {
  title: string
  source: string
  provision_type: string
  content: string
  score?: number | null
  ipc_counterpart?: string | null
  bns_section?: string | null
  cognizable?: boolean | null
  bailable?: boolean | null
}

export interface LegalResearchOutput {
  query: string
  provisions: LegalProvisionItem[]
  citations: string[]
  statutory_notes: string
}

export interface SimilarCaseItem {
  reference_id: string
  summary: string
  category?: string | null
  score: number
  metadata: Record<string, any>
}

export interface SimilarCaseOutput {
  query: string
  cases: SimilarCaseItem[]
  disclaimer: string
}

export interface InvestigationReportOutput {
  report_id: string
  case_identifier?: string | null
  title: string
  executive_summary: string
  parties_involved: Record<string, any>
  established_facts: string[]
  allegations_and_uncertainties: string[]
  evidence_provenance_summary: string
  contradictions_and_gaps: string[]
  applicable_legal_framework: string[]
  suggested_investigator_actions: string[]
  human_review_notice: string
  generated_at: string
  formatted_markdown: string
}

export interface AgentRunRequest {
  message: string
  complaint_id?: string | null
  conversation_id?: string | null
  tools_allowed?: string[] | null
  history?: Array<{ role: string; content: string }>
}

export interface AgentRunResponse {
  conversation_id: string
  answer: string
  execution_status: 'completed' | 'partial' | 'failed' | 'action_blocked'
  intent: string
  selected_tools: string[]
  tool_executions: ToolExecutionRecord[]
  complaint_analysis?: ComplaintAnalysisOutput | null
  evidence_provenance?: EvidenceProvenanceOutput | null
  factual_validation?: FactualValidationOutput | null
  legal_research?: LegalResearchOutput | null
  similar_cases?: SimilarCaseOutput | null
  investigation_report?: InvestigationReportOutput | null
  follow_up_questions: string[]
  requires_human_approval: boolean
  approval_message?: string | null
}

export interface ToolInfo {
  name: string
  display_name: string
  description: string
}

export interface CaseSummaryItem {
  id: string
  reference_id: string
  title: string
  incident_date?: string | null
  incident_location?: string | null
  status: string
}

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
  // AI Investigation Agent Run
  agentRun: (data: AgentRunRequest) =>
    apiClient.post<AgentRunResponse>('/assistant/agent/run', data).then((r) => r.data),

  // Available Tools
  listTools: () =>
    apiClient.get<{ tools: ToolInfo[] }>('/assistant/tools').then((r) => r.data),

  // Search/List Complaints for Docket Selector
  listCases: (search?: string) =>
    apiClient
      .get<CaseSummaryItem[]>('/assistant/cases', { params: { search } })
      .then((r) => r.data),

  // Legacy RAG query (backward compatible)
  query: (data: AssistantQueryRequest) =>
    apiClient.post<AssistantQueryResponse>('/assistant/query', data).then((r) => r.data),
}
