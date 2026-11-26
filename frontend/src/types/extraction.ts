// types/extraction.ts
export type EntityType = 'PERSON' | 'LOCATION' | 'DATE' | 'TIME' | 'ORG' | 'OTHER'

export interface ExtractedEntity {
  id: string
  text: string
  entity_type: EntityType
  start_char: number
  end_char: number
  confidence: number
  source_sentence?: string
}

export interface ExtractedFact {
  id: string
  fact_text: string
  confidence: number
  source_span?: EvidenceSpan
  entities: string[]
  category?: string
}

export interface EvidenceSpan {
  id: string
  text: string
  start_char: number
  end_char: number
  entity_type?: EntityType
  fact_id?: string
}

export interface ExtractionResult {
  complaint_id: string
  entities: ExtractedEntity[]
  facts: ExtractedFact[]
  evidence_spans: EvidenceSpan[]
  processed_at: string
}
