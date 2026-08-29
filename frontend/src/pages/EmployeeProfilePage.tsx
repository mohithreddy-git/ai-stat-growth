import { ArrowRight, BriefcaseBusiness, GraduationCap, Target, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { AppShell } from '../components/AppShell'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '../components/Phase2UI'
import { api } from '../services/api'
import type { EmployeeProfile } from '../types'

export function EmployeeProfilePage() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<EmployeeProfile | null>(null)
  const [error, setError] = useState('')

  const load = () => {
    if (!user) return
    setError('')
    api.profile(user.id).then(setProfile).catch((err) => setError(err instanceof Error ? err.message : 'Unable to load employee profile'))
  }
  useEffect(load, [user?.id])

  return <AppShell><div className="animate-rise"><PageHeader eyebrow="Employee profile · Step 01" title="Your official profile" description="This context helps the platform interpret role requirements and tailor the next learning action." action={<Link className="primary-button" to="/employee/competencies">View competencies <ArrowRight size={16} /></Link>} />
    <div className="mt-8">{error ? <ErrorState message={error} onRetry={load} /> : !profile ? <LoadingState label="Loading employee profile…" /> : <ProfileContent profile={profile} />}</div>
  </div></AppShell>
}

function ProfileContent({ profile }: { profile: EmployeeProfile }) {
  const details = [
    ['Employee ID', profile.employee_id], ['Designation', profile.designation], ['Department', profile.department], ['Division', profile.division], ['Current assignment', profile.current_assignment], ['Years of experience', `${profile.years_experience} years`], ['Education', profile.educational_qualification], ['Domain', profile.domain],
  ]
  return <>
    <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <div className="panel bg-navy p-7 text-white sm:p-8"><div className="grid h-14 w-14 place-items-center rounded-2xl bg-teal text-lg font-bold">{profile.full_name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</div><p className="eyebrow mt-7 text-teal-200">Signed-in official</p><h2 className="mt-2 text-2xl font-semibold">{profile.full_name}</h2><p className="mt-2 text-sm text-blue-100">{profile.designation}</p><div className="mt-8 border-t border-white/10 pt-6"><p className="text-xs font-semibold uppercase tracking-wider text-blue-200">Career goal</p><p className="mt-3 text-base leading-7">{profile.career_goal}</p></div></div>
      <div className="panel p-6 sm:p-8"><div className="flex items-center gap-3"><span className="status-icon"><UserRound size={18} /></span><div><p className="eyebrow text-teal">Profile context</p><h2 className="mt-1 text-lg font-semibold text-navy">Role and assignment details</h2></div></div><dl className="mt-7 grid gap-x-8 gap-y-6 sm:grid-cols-2">{details.map(([label, value]) => <div key={label} className="border-b border-line pb-4"><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt><dd className="mt-2 text-sm font-semibold leading-6 text-navy">{value || 'Not provided'}</dd></div>)}</dl></div>
    </section>
    <section className="mt-6 grid gap-6 lg:grid-cols-2"><div className="panel p-6"><div className="flex items-center gap-3"><span className="status-icon"><GraduationCap size={18} /></span><div><p className="eyebrow text-teal">Learning history</p><h2 className="mt-1 text-lg font-semibold text-navy">Previous training</h2></div></div>{profile.previous_trainings.length ? <ul className="mt-5 space-y-3">{profile.previous_trainings.map((training) => <li className="flex items-start gap-3 text-sm leading-6 text-slate-600" key={training}><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-teal" />{training}</li>)}</ul> : <div className="mt-5"><EmptyState title="No completed training recorded" detail="Your completed learning will appear here." /></div>}</div><div className="panel p-6"><div className="flex items-center gap-3"><span className="status-icon"><BriefcaseBusiness size={18} /></span><div><p className="eyebrow text-teal">Next context signal</p><h2 className="mt-1 text-lg font-semibold text-navy">Why this profile matters</h2></div></div><p className="mt-5 text-sm leading-7 text-slate-600">Your current assignment and career goal are used alongside assessed competency scores to distinguish an urgent role gap from an optional development area.</p><div className="mt-6 rounded-xl border border-teal/20 bg-[#f4fbfa] p-4"><div className="flex items-start gap-3"><Target className="mt-0.5 shrink-0 text-teal" size={18} /><p className="text-sm font-medium leading-6 text-navy">Continue to your competency profile to see how your current capability compares with role targets.</p></div></div></div></section>
  </>
}
