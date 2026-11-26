// types/complaint.ts
export type ComplaintStatus =
  | 'uploaded'
  | 'processing'
  | 'draft_generated'
  | 'validation_required'
  | 'under_review'
  | 'reviewed'
  | 'archived'

export interface Complaint {
  id: string
  reference_id: string
  title: string
  raw_text: string
  extracted_text?: string
  language: string
  incident_date?: string
  incident_location?: string
  status: ComplaintStatus
  submitted_by: string
  created_at: string
  updated_at: string
  category?: string
  file_name?: string
  structured_data?: Record<string, any>
}

export interface ComplaintListItem {
  id: string
  reference_id: string
  title: string
  status: ComplaintStatus
  submitted_by: string
  created_at: string
  category?: string
  incident_date?: string
  incident_location?: string
}

export interface CreateComplaintRequest {
  title: string
  reference_id: string
  language: string
  incident_date?: string
  incident_location?: string
  raw_text?: string
}

export interface UploadComplaintRequest extends CreateComplaintRequest {
  file: File
}

export interface ComplaintListResponse {
  items: ComplaintListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
