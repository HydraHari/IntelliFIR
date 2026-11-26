import React from 'react'
import { Link } from 'react-router-dom'
import { ShieldAlert, ArrowLeft } from 'lucide-react'
import { Button } from '../components/ui/button'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center p-6 bg-slate-50 text-center">
      <div className="h-16 w-16 rounded-2xl bg-navy-50 flex items-center justify-center text-navy-800 mb-4">
        <ShieldAlert className="h-8 w-8 text-navy-800" />
      </div>
      <h1 className="text-3xl font-extrabold text-navy-950">404 — Page Not Found</h1>
      <p className="text-sm text-slate-500 mt-2 max-w-sm">
        The requested record or navigation route does not exist in the IntelliFIR registry.
      </p>
      <Link to="/dashboard" className="mt-6">
        <Button variant="primary" className="gap-2 text-xs">
          <ArrowLeft className="h-4 w-4" />
          <span>Return to Dashboard</span>
        </Button>
      </Link>
    </div>
  )
}
