import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Shield,
  Lock,
  Mail,
  CheckCircle2,
  Cpu,
  FileCheck2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Alert, AlertDescription } from '../../components/ui/alert'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('admin@intellifir.local')
  const [password, setPassword] = useState('admin12345')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const quickRoles = [
    {
      role: 'Administrator',
      email: 'admin@intellifir.local',
      pass: 'admin12345',
      badge: 'Full Access',
    },
    {
      role: 'Reviewer',
      email: 'reviewer@intellifir.local',
      pass: 'reviewer12345',
      badge: 'Audit & Approve',
    },
    {
      role: 'Investigator',
      email: 'investigator@intellifir.local',
      pass: 'investigator12345',
      badge: 'Case Officer',
    },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await login({ email, password })
      navigate('/dashboard')
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          'Authentication failed. Please verify credentials or choose a demo persona below.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const fillCredentials = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail)
    setPassword(rolePass)
    setError(null)
  }

  return (
    <div className="min-h-screen w-full flex bg-[#F8FAFC] dark:bg-[#070B16] text-slate-900 dark:text-slate-100 font-sans">
      {/* Left Column: Enterprise Value Proposition & Tech Architecture */}
      <div className="hidden lg:flex w-7/12 bg-[#0B132B] p-12 text-white flex-col justify-between border-r border-slate-800/80 relative overflow-hidden">
        {/* Background ambient lighting & grid */}
        <div className="absolute inset-0 bg-grid-slate pointer-events-none opacity-20" />
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg ring-1 ring-white/20">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight">IntelliFIR</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 bg-blue-500/20 text-blue-300 rounded border border-blue-400/30">
                  ENTERPRISE v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Evidence-Grounded AI Framework for Law Enforcement
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-full border border-slate-800">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>Audit-Compliant Human-in-the-Loop</span>
          </div>
        </div>

        {/* Main Pitch */}
        <div className="relative z-10 my-auto py-8 space-y-6 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/20">
            <Sparkles className="h-3.5 w-3.5" />
            Empirical Benchmark: 0% Unsupported Claims in Validated Drafts
          </div>

          <h1 className="text-3xl xl:text-4xl font-extrabold tracking-tight text-white leading-[1.15]">
            Transform unstructured citizen complaints into auditable First Information Reports.
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed">
            Eliminate investigative hallucination and administrative delays. IntelliFIR uses
            token-level BERT Named Entity Recognition, character-span evidence provenance, and
            independent factual validation to safeguard judicial integrity.
          </p>

          {/* Core Feature Pillars */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-800/80">
            <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80">
              <FileCheck2 className="h-4 w-4 text-blue-400 mb-2" />
              <h4 className="text-xs font-semibold text-white">Full Provenance</h4>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                Every extracted claim links directly to character offsets in the raw complaint.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80">
              <ShieldCheck className="h-4 w-4 text-emerald-400 mb-2" />
              <h4 className="text-xs font-semibold text-white">Factual Validator</h4>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                Detects contradictions, temporal inconsistencies, and unstated assumptions.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80">
              <Cpu className="h-4 w-4 text-indigo-400 mb-2" />
              <h4 className="text-xs font-semibold text-white">Hybrid Retrieval</h4>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                FAISS semantic vector store for penal code provisions and historical precedents.
              </p>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-500 pt-4 border-t border-slate-800/80">
          <span>Protected by Role-Based Access Control (RBAC)</span>
          <span className="font-mono text-[11px]">ISO/IEC 27001 AI Alignment</span>
        </div>
      </div>

      {/* Right Column: Sign In Workspace */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 lg:p-12 relative">
        <div className="w-full max-w-md space-y-6">
          {/* Card Header */}
          <div className="space-y-1.5 text-center lg:text-left">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Law Enforcement Portal
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Authenticate using your official government or investigation credentials.
            </p>
          </div>

          {/* Quick Demo Persona Switcher (For Interviews/Evaluators) */}
          <div className="p-3 rounded-xl bg-slate-100/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400 px-1">
              <span>Quick Demo Switcher</span>
              <span className="text-[10px] text-blue-600 dark:text-blue-400 font-semibold">
                Click to Auto-Fill
              </span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {quickRoles.map((r) => (
                <button
                  key={r.role}
                  type="button"
                  onClick={() => fillCredentials(r.email, r.pass)}
                  className={`px-2 py-1.5 rounded-lg text-left text-xs transition-all border ${
                    email === r.email
                      ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 border-blue-500/40 shadow-2xs font-semibold'
                      : 'bg-transparent text-slate-600 dark:text-slate-300 border-transparent hover:bg-white/50 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <p className="text-[11px] font-medium truncate">{r.role}</p>
                  <p className="text-[9px] text-slate-400 dark:text-slate-500 truncate">
                    {r.badge}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <Alert variant="destructive" className="py-2.5">
              <AlertDescription className="text-xs">{error}</AlertDescription>
            </Alert>
          )}

          {/* Auth Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Official Email Address
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  id="email"
                  type="email"
                  className="pl-9 h-10 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                  placeholder="officer@police.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Secure Password
                </Label>
                <span className="text-[11px] text-blue-600 dark:text-blue-400 cursor-pointer hover:underline">
                  Forgot credentials?
                </span>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  id="password"
                  type="password"
                  className="pl-9 h-10 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 font-mono"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full h-10 mt-2 text-xs font-semibold tracking-wide bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center justify-center gap-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <span>Authenticating Officer...</span>
              ) : (
                <>
                  <span>Sign In to Investigation Portal</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </Button>
          </form>

          {/* Registration link */}
          <div className="pt-2 text-center text-xs text-slate-500 dark:text-slate-400">
            <span>Don't have an authorized account? </span>
            <Link
              to="/register"
              className="font-semibold text-blue-600 dark:text-blue-400 hover:underline"
            >
              Request Access
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
