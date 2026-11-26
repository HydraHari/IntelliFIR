import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  FileUp,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileSpreadsheet,
  X,
  Languages,
  Calendar,
  MapPin,
  Cpu,
} from 'lucide-react'
import { complaintsApi } from '../api/complaints'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import { Alert, AlertDescription } from '../components/ui/alert'

export const ComplaintUploadPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const defaultTab = searchParams.get('tab') === 'manual' ? 'manual' : 'upload'

  // Shared Form State
  const [title, setTitle] = useState('')
  const [language, setLanguage] = useState('en')
  const [incidentDate, setIncidentDate] = useState('')
  const [incidentLocation, setIncidentLocation] = useState('')

  // Upload Tab State
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  // Manual Tab State
  const [rawText, setRawText] = useState('')

  // Process State
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      setFile(droppedFile)
      if (!title) {
        setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''))
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0]
      setFile(selected)
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, ''))
      }
    }
  }

  const handleSubmitUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please select or drop a complaint document to upload.')
      return
    }
    setError(null)
    setIsSubmitting(true)

    const formData = new FormData()
    formData.append('title', title)
    formData.append('language', language)
    if (incidentDate) formData.append('incident_date', incidentDate)
    if (incidentLocation) formData.append('incident_location', incidentLocation)
    formData.append('file', file)

    try {
      const resp = await complaintsApi.upload(formData)
      navigate(`/cases/${resp.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Document upload and OCR extraction failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSubmitManual = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rawText || rawText.trim().length < 20) {
      setError('Please provide at least 20 characters of citizen complaint statement.')
      return
    }
    setError(null)
    setIsSubmitting(true)

    try {
      const resp = await complaintsApi.create({
        title,
        reference_id: '',
        language,
        incident_date: incidentDate || undefined,
        incident_location: incidentLocation || undefined,
        raw_text: rawText,
      })
      navigate(`/cases/${resp.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to submit complaint statement.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const loadScenario = (type: 'burglary' | 'cyber' | 'robbery') => {
    if (type === 'burglary') {
      setTitle('House Burglary and Theft of Gold Jewelry in Apartment')
      setIncidentDate('2026-11-03')
      setIncidentLocation('Flat 402, Shanti Heights, Indirapuram')
      setRawText(
        'To the Station House Officer. I, Vikram Adani, resident of Flat 402, Shanti Heights, Indirapuram, ' +
          'wish to report a burglary at my flat. Sometime between 10:00 AM and 6:00 PM on 03/11/2026, when my family was away at work, ' +
          'unknown person or persons entered by breaking the main door wooden latch. They stole approximately 50 grams ' +
          'of gold ornaments worth Rs. 3,50,000 from the bedroom almirah. The building security guard Ramesh stated he noticed ' +
          'two men in delivery uniforms around 2:00 PM. I request an urgent investigation.'
      )
    } else if (type === 'cyber') {
      setTitle('Online Banking Fraud and Unauthorized Account Debit via Phishing')
      setIncidentDate('2026-09-28')
      setIncidentLocation('Online / Sector 18, Noida')
      setRawText(
        'My name is Priya Sharma, residing at Sector 18, Noida. On 28/09/2026 at approximately 3:15 PM, ' +
          'I received a telephone call from a person claiming to be a customer care representative of ABC Bank. ' +
          'The caller stated that my KYC verification was overdue and sent a link via SMS from sender VK-ABCBANK. ' +
          'Upon clicking the link and entering details, Rs. 75,000 was debited in two transactions to an unknown account. ' +
          'I have preserved the call recording, SMS header, and bank transaction statement as electronic evidence. ' +
          'I suspect that the caller belongs to an organized cyber fraud syndicate operating from Jharkhand.'
      )
    } else {
      setTitle('Armed Robbery of Mobile Phone and Wallet near Metro Station')
      setIncidentDate('2026-10-12')
      setIncidentLocation('Inner Circle, Connaught Place, New Delhi')
      setRawText(
        'I, Rajesh Kumar, son of Mohan Kumar, resident of 14B Green Park, New Delhi, ' +
          'hereby report that on 12/10/2026 at around 8:30 PM, I was walking near the Inner Circle, ' +
          'Connaught Place, opposite Regal Building. Two unidentified men riding a black motorcycle ' +
          'with no visible registration plate intercepted me. The pillion rider brandished a knife ' +
          'and snatched my Apple iPhone 14 and leather wallet containing Rs. 4,500 in cash and my Driving License. ' +
          'A nearby street tea-vendor named Suresh saw the incident occur. The perpetrators fled towards Barakhamba Road. ' +
          'CCTV cameras installed outside the nearby bank may have captured the escape route.'
      )
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Complaint Ingestion & Text Extraction
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-medium">
              Stage 1
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Ingest unstructured citizen statements via scanned document upload or direct narrative transcription.
          </p>
        </div>

        {/* Quick Demo Pre-fill Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
            Demo Scenarios:
          </span>
          <button
            type="button"
            onClick={() => loadScenario('robbery')}
            className="px-2 py-1 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors"
          >
            Robbery
          </button>
          <button
            type="button"
            onClick={() => loadScenario('cyber')}
            className="px-2 py-1 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors"
          >
            Cyber Fraud
          </button>
          <button
            type="button"
            onClick={() => loadScenario('burglary')}
            className="px-2 py-1 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors"
          >
            Burglary
          </button>
        </div>
      </div>

      {/* Visual Pipeline Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900 text-slate-300 text-xs flex items-center justify-between border border-slate-800">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-blue-400" />
          <span className="font-semibold text-white">Automated Processing Pipeline:</span>
          <span className="hidden md:inline text-slate-400">
            PyMuPDF / Tesseract OCR → BERT Token Classification → Evidence Provenance Indexing → FIR Draft Synthesis
          </span>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 font-semibold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
          Ready
        </span>
      </div>

      {error && (
        <Alert variant="destructive" className="py-2.5">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue={defaultTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-4 p-1 bg-slate-200/60 dark:bg-slate-800/60 rounded-lg">
          <TabsTrigger value="upload" className="gap-2 text-xs font-medium">
            <Upload className="h-3.5 w-3.5" /> Scanned Document / File Upload (PDF, Word, OCR)
          </TabsTrigger>
          <TabsTrigger value="manual" className="gap-2 text-xs font-medium">
            <FileText className="h-3.5 w-3.5" /> Direct Complaint Transcription
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Upload Document */}
        <TabsContent value="upload">
          <form onSubmit={handleSubmitUpload} className="space-y-4">
            <Card className="border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
              <CardHeader className="pb-3 pt-4 px-6 border-b border-slate-100 dark:border-slate-800">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                  Document Ingestion Zone
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Securely upload citizen complaint files (PDF, DOCX, TXT, PNG, JPG). Optical Character Recognition (OCR) is automatically applied to scanned documents.
                </CardDescription>
              </CardHeader>

              <CardContent className="p-6 space-y-4">
                {/* Drag and Drop Zone */}
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                    dragActive
                      ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30'
                      : file
                      ? 'border-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/20'
                      : 'border-slate-300 dark:border-slate-700 hover:border-slate-400 bg-slate-50/50 dark:bg-slate-900/40'
                  }`}
                  onClick={() => document.getElementById('file-upload-input')?.click()}
                >
                  <input
                    id="file-upload-input"
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.tiff"
                    onChange={handleFileChange}
                  />

                  {file ? (
                    <div className="flex flex-col items-center gap-2">
                      <div className="h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="h-5 w-5" />
                      </div>
                      <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {file.name}
                      </p>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {(file.size / 1024 / 1024).toFixed(2)} MB • Ready for OCR ingestion
                      </p>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          setFile(null)
                        }}
                        className="mt-1 text-[11px] text-rose-600 dark:text-rose-400 hover:underline flex items-center gap-1"
                      >
                        <X className="h-3 w-3" /> Remove File
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <div className="h-10 w-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 shadow-2xs">
                        <FileUp className="h-5 w-5" />
                      </div>
                      <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                        Drop official complaint file or click to browse
                      </p>
                      <p className="text-[11px] text-slate-400">
                        PDF, DOCX, TXT, or scanned image files up to 20 MB
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {['PDF', 'DOCX', 'PNG', 'JPG', 'TIFF'].map((fmt) => (
                          <span
                            key={fmt}
                            className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-200/60 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                          >
                            .{fmt}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Form Fields */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label htmlFor="upload-title" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Complaint Subject / Reference Title *
                    </Label>
                    <Input
                      id="upload-title"
                      className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                      placeholder="e.g. Armed robbery of cell phone and wallet near Metro Gate 2"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="upload-date" className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" /> Incident Date
                    </Label>
                    <Input
                      id="upload-date"
                      type="date"
                      className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                      value={incidentDate}
                      onChange={(e) => setIncidentDate(e.target.value)}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="upload-loc" className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" /> Incident Location / Jurisdiction
                    </Label>
                    <Input
                      id="upload-loc"
                      className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                      placeholder="e.g. Connaught Place, New Delhi"
                      value={incidentLocation}
                      onChange={(e) => setIncidentLocation(e.target.value)}
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full h-10 mt-3 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center justify-center gap-2"
                  disabled={isSubmitting || !file}
                >
                  {isSubmitting ? (
                    <span>Extracting Text via OCR & Processing Pipeline...</span>
                  ) : (
                    <>
                      <span>Upload & Execute Extraction Pipeline</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </form>
        </TabsContent>

        {/* Tab 2: Manual Statement Entry */}
        <TabsContent value="manual">
          <form onSubmit={handleSubmitManual} className="space-y-4">
            <Card className="border-slate-200 dark:border-slate-800 shadow-2xs bg-white dark:bg-slate-900/90">
              <CardHeader className="pb-3 pt-4 px-6 border-b border-slate-100 dark:border-slate-800">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                  Citizen Statement Transcription
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Enter verbatim statement recorded from the complainant at the police station or precinct desk.
                </CardDescription>
              </CardHeader>

              <CardContent className="p-6 space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="manual-title" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Complaint Title / Incident Summary *
                  </Label>
                  <Input
                    id="manual-title"
                    className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                    placeholder="e.g. Cyber financial fraud via fake KYC link"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="manual-date" className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" /> Incident Date
                    </Label>
                    <Input
                      id="manual-date"
                      type="date"
                      className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                      value={incidentDate}
                      onChange={(e) => setIncidentDate(e.target.value)}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="manual-loc" className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" /> Incident Location
                    </Label>
                    <Input
                      id="manual-loc"
                      className="h-9 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                      placeholder="e.g. Sector 18, Noida"
                      value={incidentLocation}
                      onChange={(e) => setIncidentLocation(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="manual-text" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Verbatim Citizen Statement Text *
                    </Label>
                    <span className="text-[11px] font-mono text-slate-400">
                      {rawText.length} characters
                    </span>
                  </div>
                  <Textarea
                    id="manual-text"
                    rows={8}
                    className="text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 font-sans leading-relaxed"
                    placeholder="Provide complainant name, incident description, date/time, suspects, witnesses, physical descriptions, stolen property..."
                    value={rawText}
                    onChange={(e) => setRawText(e.target.value)}
                    required
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full h-10 mt-3 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center justify-center gap-2"
                  disabled={isSubmitting || !rawText.trim()}
                >
                  {isSubmitting ? (
                    <span>Running BERT NER & Evidence Extraction...</span>
                  ) : (
                    <>
                      <span>Submit Statement & Begin AI Pipeline</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </form>
        </TabsContent>
      </Tabs>
    </div>
  )
}
