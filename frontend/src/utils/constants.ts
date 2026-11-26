// utils/constants.ts
export const APP_NAME = 'IntelliFIR'
export const APP_TAGLINE = 'AI-Powered FIR Drafting Platform'

export const COMPLAINT_STATUSES = [
  'uploaded',
  'processing',
  'draft_generated',
  'validation_required',
  'under_review',
  'reviewed',
  'archived',
] as const

export const ENTITY_TYPES = ['PERSON', 'LOCATION', 'DATE', 'TIME', 'ORG', 'OTHER'] as const

export const ENTITY_COLORS: Record<string, string> = {
  PERSON: 'bg-blue-100 text-blue-800 border-blue-200',
  LOCATION: 'bg-green-100 text-green-800 border-green-200',
  DATE: 'bg-purple-100 text-purple-800 border-purple-200',
  TIME: 'bg-purple-100 text-purple-800 border-purple-200',
  ORG: 'bg-orange-100 text-orange-800 border-orange-200',
  OTHER: 'bg-gray-100 text-gray-700 border-gray-200',
}

export const ENTITY_HIGHLIGHT_COLORS: Record<string, string> = {
  PERSON: 'bg-blue-100',
  LOCATION: 'bg-green-100',
  DATE: 'bg-purple-100',
  TIME: 'bg-purple-100',
  ORG: 'bg-orange-100',
  OTHER: 'bg-gray-100',
}

export const SUPPORTED_FILE_TYPES = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png']
export const MAX_FILE_SIZE_MB = 20
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

export const SIMILARITY_THRESHOLD = 0.7

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'
