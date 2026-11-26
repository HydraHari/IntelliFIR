import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'

import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { ComplaintUploadPage } from './pages/ComplaintUploadPage'
import { CaseListPage } from './pages/CaseListPage'
import { CaseDetailPage } from './pages/CaseDetailPage'
import { EvidenceViewerPage } from './pages/EvidenceViewerPage'
import { DraftPage } from './pages/DraftPage'
import { ValidationReportPage } from './pages/ValidationReportPage'
import { SimilarCasesPage } from './pages/SimilarCasesPage'
import { LegalRetrievalPage } from './pages/LegalRetrievalPage'
import { AssistantPage } from './pages/AssistantPage'
import { ModelsPage } from './pages/ModelsPage'
import { EvaluationPage } from './pages/EvaluationPage'
import { NotFoundPage } from './pages/NotFoundPage'

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="complaints/upload" element={<ComplaintUploadPage />} />
            <Route path="cases" element={<CaseListPage />} />
            <Route path="cases/:id" element={<CaseDetailPage />} />
            <Route path="cases/:id/evidence" element={<EvidenceViewerPage />} />
            <Route path="cases/:id/draft" element={<DraftPage />} />
            <Route path="cases/:id/validation" element={<ValidationReportPage />} />
            <Route path="similar-cases" element={<SimilarCasesPage />} />
            <Route path="legal" element={<LegalRetrievalPage />} />
            <Route path="assistant" element={<AssistantPage />} />
            <Route path="models" element={<ModelsPage />} />
            <Route path="evaluation" element={<EvaluationPage />} />
          </Route>

          {/* 404 Catch-All */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
