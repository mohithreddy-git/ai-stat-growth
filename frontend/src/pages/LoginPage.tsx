import { useEffect, useState } from 'react'
import { ArrowRight, BarChart3, CheckCircle2, Eye, EyeOff, LockKeyhole, ShieldCheck, Sparkles } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import type { Role } from '../types'

const demos: { role: Role; name: string; email: string; detail: string }[] = [
  { role: 'EMPLOYEE', name: 'Employee demo', email: 'employee.demo@aistatgrowth.gov.in', detail: 'Explore your competency starting point' },
  { role: 'ADMIN', name: 'Admin demo', email: 'admin.demo@aistatgrowth.gov.in', detail: 'Preview workforce intelligence controls' },
  { role: 'TRAINER', name: 'Trainer demo', email: 'trainer.demo@aistatgrowth.gov.in', detail: 'Preview assessment authoring workspace' },
]

export function LoginPage() {
  const { user, signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('employee.demo@aistatgrowth.gov.in')
  const [password, setPassword] = useState('Demo@123')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (user) navigate(`/${user.role.toLowerCase()}/dashboard`, { replace: true })
  }, [navigate, user])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await signIn(email, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from || '/employee/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in')
    } finally {
      setIsSubmitting(false)
    }
  }

  return <div className="min-h-screen bg-mist lg:grid lg:grid-cols-[0.95fr_1.05fr]">
    <section className="relative hidden overflow-hidden bg-navy px-12 py-14 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
      <div className="absolute -right-24 top-24 h-80 w-80 rounded-full border border-white/10" /><div className="absolute -right-10 top-38 h-52 w-52 rounded-full border border-white/10" />
      <div><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-teal"><BarChart3 size={22} /></span><span className="text-sm font-bold tracking-[0.17em]">AI STAT-GROWTH</span></div><div className="mt-20 max-w-xl"><p className="eyebrow text-teal-200">Official statistics · capability intelligence</p><h1 className="mt-5 text-5xl font-semibold leading-[1.08] tracking-tight xl:text-6xl">Turn capability gaps into measurable growth.</h1><p className="mt-7 max-w-lg text-lg leading-8 text-blue-100">A trusted foundation for continuously mapping workforce capability to the evolving needs of India’s Official Statistical System.</p></div></div>
      <div className="grid max-w-xl gap-4 sm:grid-cols-3"><div className="border-t border-white/20 pt-4"><p className="text-2xl font-semibold">50</p><p className="mt-1 text-xs text-blue-200">synthetic officials</p></div><div className="border-t border-white/20 pt-4"><p className="text-2xl font-semibold">35</p><p className="mt-1 text-xs text-blue-200">competencies mapped</p></div><div className="border-t border-white/20 pt-4"><p className="text-2xl font-semibold">Zero-cost</p><p className="mt-1 text-xs text-blue-200">mock-first AI mode</p></div></div>
    </section>
    <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8"><div className="w-full max-w-lg"><div className="mb-9 lg:hidden"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-navy text-white"><BarChart3 size={20} /></span><span className="text-sm font-bold tracking-[0.15em] text-navy">AI STAT-GROWTH</span></div></div><div className="mb-8"><p className="eyebrow text-teal">Secure demonstration environment</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-navy">Welcome back</h2><p className="mt-2 text-sm leading-6 text-slate-600">Sign in to enter your role-specific workspace.</p></div>
      <div className="mb-7 grid gap-2 sm:grid-cols-3">{demos.map((demo) => <button key={demo.role} type="button" onClick={() => { setEmail(demo.email); setPassword('Demo@123'); setError('') }} className={`demo-role ${email === demo.email ? 'demo-role-active' : ''}`}><span>{demo.name.replace(' demo', '')}</span><span className="mt-1 block text-[10px] font-medium uppercase tracking-wide opacity-70">{demo.role}</span></button>)}</div>
      <form onSubmit={submit} className="space-y-5"><label className="field-label">Work email<input className="field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" required /></label><label className="field-label">Password<div className="relative"><input className="field pr-11" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /><button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-navy" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((value) => !value)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>{error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}<button className="primary-button w-full" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Enter workspace'}<ArrowRight size={17} /></button></form>
      <div className="mt-8 grid gap-3 rounded-2xl border border-line bg-white p-4 text-xs text-slate-600 shadow-soft sm:grid-cols-3"><div className="flex gap-2"><ShieldCheck className="shrink-0 text-teal" size={16} /><span>Role-based access</span></div><div className="flex gap-2"><LockKeyhole className="shrink-0 text-teal" size={16} /><span>Signed session</span></div><div className="flex gap-2"><Sparkles className="shrink-0 text-teal" size={16} /><span>Mock-first AI</span></div></div><p className="mt-7 flex items-center justify-center gap-1.5 text-center text-xs text-slate-500"><CheckCircle2 size={14} className="text-teal" /> Synthetic demo accounts · Phase 1 foundation</p></div></section>
  </div>
}
