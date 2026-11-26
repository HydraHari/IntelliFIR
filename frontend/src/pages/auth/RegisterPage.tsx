import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, User as UserIcon, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Alert, AlertDescription } from '../../components/ui/alert'

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'admin' | 'officer' | 'reviewer'>('officer')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await register({
        full_name: fullName,
        email,
        password,
        role,
      })
      navigate('/dashboard')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Registration failed. Please check inputs.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#F8FAFC] dark:bg-[#070B16] p-6 relative">
      <div className="w-full max-w-lg space-y-6 bg-white dark:bg-slate-900/90 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative z-10">
        {/* Brand Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm ring-1 ring-white/20">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Request Officer Account
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Register for authorized access to the IntelliFIR case drafting pipeline.
            </p>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="py-2.5">
            <AlertDescription className="text-xs">{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="fullName" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Full Legal Name & Rank
            </Label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                id="fullName"
                className="pl-9 h-10 text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                placeholder="Inspector Ramesh Rao"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Official Police / Judicial Email
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
            <Label htmlFor="password" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Password (Minimum 8 Characters)
            </Label>
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

          <div className="space-y-1.5">
            <Label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Operational Role & Permission Tier
            </Label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'officer', title: 'Investigator', desc: 'Ingest & Draft' },
                { id: 'reviewer', title: 'Reviewer', desc: 'Factual Audit' },
                { id: 'admin', title: 'Administrator', desc: 'System Config' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setRole(item.id as any)}
                  className={`p-2.5 rounded-lg border text-left transition-all ${
                    role === item.id
                      ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/40 text-blue-900 dark:text-blue-200 ring-1 ring-blue-500/20'
                      : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <p className="text-xs font-semibold">{item.title}</p>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{item.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full h-10 mt-3 text-xs font-semibold tracking-wide bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center justify-center gap-2"
            disabled={isLoading}
          >
            {isLoading ? (
              <span>Creating Account...</span>
            ) : (
              <>
                <span>Complete Registration</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </>
            )}
          </Button>
        </form>

        <div className="pt-2 text-center text-xs text-slate-500 dark:text-slate-400">
          <span>Already registered? </span>
          <Link to="/login" className="font-semibold text-blue-600 dark:text-blue-400 hover:underline">
            Sign In Here
          </Link>
        </div>
      </div>
    </div>
  )
}
