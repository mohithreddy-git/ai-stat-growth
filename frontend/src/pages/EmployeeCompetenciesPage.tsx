import { ArrowRight, BarChart3, CheckCircle2, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../i18n'
import { AppShell } from '../components/AppShell'
import { DeltaBadge, EmptyState, ErrorState, LevelPill, LoadingState, PageHeader, RadarChart, ScoreBar } from '../components/Phase2UI'
import { api } from '../services/api'
import type { CompetencyDomainSummary, CompetencyProfile, EmployeeCompetency, EmployeeProfile, FRACProfile, LearningResource, SkillGap } from '../types'

const categoryLabels: Record<string, string> = { 'Behavioural & Managerial': 'Behavioural and managerial', 'Digital Governance': 'Digital governance', Technical: 'Technical', Statistical: 'Statistical' }

export function EmployeeCompetenciesPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const [data, setData] = useState<{ profile: CompetencyProfile; domainSummary: CompetencyDomainSummary; employeeProfile: EmployeeProfile; frac: FRACProfile; gaps: SkillGap[]; recommendations: LearningResource[] } | null>(null)
  const [error, setError] = useState('')
  const load = async () => {
    if (!user) return
    setError('')
    try {
      const [profile, domainSummary, employeeProfile, frac, gaps, recommendations] = await Promise.all([
        api.competencies(user.id),
        api.competencyDomainSummary(user.id),
        api.profile(user.id),
        api.fracProfile(user.id),
        api.skillGaps(user.id),
        api.recommendations(user.id),
      ])
      setData({ profile, domainSummary, employeeProfile, frac, gaps, recommendations })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load competency intelligence')
    }
  }
  useEffect(() => { void load() }, [user?.id])

  return <AppShell><div className="animate-rise"><PageHeader eyebrow={`Competency profile · ${t('myCompetencies')}`} title={t('myCompetencies')} description="Current scores are persisted in the competency model and update when assessment evidence is submitted." action={<Link className="primary-button" to="/employee/assessment">Take assessment <ArrowRight size={16} /></Link>} />
    <div className="mt-8">{error ? <ErrorState message={error} onRetry={() => void load()} /> : !data ? <LoadingState label="Loading competency intelligence…" /> : <ProfileContent {...data} />}</div>
  </div></AppShell>
}

function ProfileContent({ profile, domainSummary, employeeProfile, frac, gaps, recommendations }: { profile: CompetencyProfile; domainSummary: CompetencyDomainSummary; employeeProfile: EmployeeProfile; frac: FRACProfile; gaps: SkillGap[]; recommendations: LearningResource[] }) {
  const categories = useMemo(() => Object.entries(profile.category_scores).sort((a, b) => b[1] - a[1]), [profile.category_scores])
  return <>
    <DomainSummaryCard summary={domainSummary} />
    <DerivationPanel profile={profile} employeeProfile={employeeProfile} frac={frac} gaps={gaps} recommendations={recommendations} />
    <section className="grid gap-6 xl:grid-cols-[0.78fr_1.22fr]"><div className="panel p-6 sm:p-8"><div className="flex items-start justify-between"><div><p className="eyebrow text-teal">Weighted readiness</p><p className="mt-2 text-4xl font-semibold tracking-tight text-navy">{profile.overall_readiness}%</p><p className="mt-2 text-sm leading-6 text-slate-600">A weighted view across all mapped competencies. The target marker on each bar is the required role level.</p></div><span className="status-icon"><Target size={19} /></span></div><div className="mt-8 space-y-5">{categories.map(([category, score]) => <div key={category}><div className="flex items-center justify-between gap-4 text-sm"><span className="font-semibold text-navy">{categoryLabels[category] || category}</span><span className="font-bold text-teal">{score}%</span></div><div className="mt-2"><ScoreBar value={score} showTarget={false} /></div></div>)}</div></div><div className="panel p-6 sm:p-8"><div className="flex items-start justify-between"><div><p className="eyebrow text-teal">Capability shape</p><h2 className="mt-2 text-xl font-semibold text-navy">Category overview</h2></div><BarChart3 className="text-teal" size={20} /></div><div className="mt-4"><RadarChart values={profile.category_scores} size={310} /></div></div></section>
    <section className="mt-8 grid gap-6 lg:grid-cols-2"><CompetencyHighlights title="Strengths" detail="Capabilities currently at or above the evidence threshold." items={profile.strengths} tone="teal" /><CompetencyHighlights title="Development focus" detail="The five lowest current scores are shown here for prioritisation." items={profile.weaknesses} tone="amber" /></section>
    <section className="mt-8"><div className="flex items-end justify-between gap-4"><div><p className="eyebrow text-teal">Full framework · {profile.competencies.length} mapped</p><h2 className="mt-2 text-xl font-semibold text-navy">Individual competency scores</h2></div><Link className="text-sm font-semibold text-teal hover:text-navy" to="/employee/skill-gaps">View prioritised gaps <ArrowRight className="ml-1 inline" size={15} /></Link></div><div className="mt-5 grid gap-3">{profile.competencies.map((item) => <CompetencyRow item={item} key={item.competency_id} />)}</div></section>
  </>
}

function DomainSummaryCard({ summary }: { summary: CompetencyDomainSummary }) {
  const domainTones = ['bg-[#eef7f6] text-teal', 'bg-[#eef3fb] text-navy', 'bg-[#fff7e8] text-[#a86400]', 'bg-[#f4effb] text-[#6b46a1]']
  const formatScore = (score: number | null) => score === null ? 'Not provided' : `${score}%`
  return <section className="panel mt-6 p-6 sm:p-8"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow text-teal">Framework composition · database summary</p><h2 className="mt-2 text-xl font-semibold text-navy">Competency domains</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">The framework composition is counted from the authoritative competency records, while the score lines reflect this employee’s current evidence and role targets.</p></div><span className="status-icon"><BarChart3 size={18} /></span></div><div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{summary.domains.map((domain, index) => <div className="rounded-xl border border-line p-4" key={domain.name}><div className="flex items-start justify-between gap-3"><span className={`rounded-lg px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${domainTones[index % domainTones.length]}`}>{domain.name}</span><span className="text-2xl font-semibold text-navy">{domain.count}</span></div><p className="mt-3 text-xs text-slate-500">Current {formatScore(domain.average_current_score)} · target {formatScore(domain.average_target_score)}</p></div>)}</div><div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5"><span className="text-sm font-semibold text-navy">Total Competencies</span><span className="rounded-full bg-navy px-3 py-1.5 text-sm font-bold text-white">{summary.total_competencies}</span></div></section>
}

function DerivationPanel({ profile, employeeProfile, frac, gaps, recommendations }: { profile: CompetencyProfile; employeeProfile: EmployeeProfile; frac: FRACProfile; gaps: SkillGap[]; recommendations: LearningResource[] }) {
  const activityNames = [...new Set(frac.activities.map((item) => item.activity))]
  const requiredNames = [...new Set(frac.competencies.map((item) => item.competency))]
  const topGap = gaps[0]
  const topRecommendation = recommendations[0]
  const context = [
    ['Designation', employeeProfile.designation],
    ['Department', employeeProfile.department],
    ['Job role', employeeProfile.current_role],
    ['Current assignment', employeeProfile.current_assignment],
    ['Qualifications', employeeProfile.educational_qualification],
    ['Experience', `${employeeProfile.years_experience} years`],
    ['Previous training', employeeProfile.previous_trainings.length ? employeeProfile.previous_trainings.join(', ') : 'Not provided'],
  ]
  const chain = ['Employee context', frac.position || 'Position not mapped', frac.role || 'Role not mapped', `${activityNames.length} activities`, `${requiredNames.length} required competencies`, `${profile.competencies.length} current competencies`, `${gaps.filter((item) => item.gap > 0).length} active gaps`, `${recommendations.length} recommendations`]
  return <section className="panel mt-6 p-6 sm:p-8"><div className="flex items-start gap-3"><span className="status-icon"><Target size={18} /></span><div><p className="eyebrow text-teal">Explainability · profile provenance</p><h2 className="mt-2 text-xl font-semibold text-navy">How was my competency profile derived?</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">The platform combines your official context with the database-mapped FRAC role and evidence-backed competency records. Missing profile signals are shown honestly.</p></div></div><div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{context.map(([label, value]) => <div className="rounded-xl border border-line bg-slate-50 p-4" key={label}><p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-sm font-semibold leading-5 text-navy">{value || 'Not provided'}</p></div>)}</div><div className="mt-6 rounded-2xl border border-teal/20 bg-[#f4fbfa] p-5"><p className="text-xs font-bold uppercase tracking-wide text-teal">FRAC and adaptive learning chain</p><div className="mt-4 flex flex-wrap items-center gap-2 text-xs font-semibold text-navy">{chain.map((step, index) => <span className="inline-flex items-center gap-2" key={`${step}-${index}`}><span className="rounded-full bg-white px-3 py-2 shadow-sm">{step}</span>{index < chain.length - 1 && <ArrowRight size={14} className="text-teal" />}</span>)}</div><div className="mt-5 grid gap-4 border-t border-teal/10 pt-5 lg:grid-cols-2"><div><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Role requirements</p><p className="mt-2 text-sm leading-6 text-slate-700">{activityNames.length ? `${activityNames.join(', ')} require ${requiredNames.slice(0, 5).join(', ')}${requiredNames.length > 5 ? ' and other mapped competencies' : ''}.` : 'Not provided'}</p></div><div><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Current decision signal</p><p className="mt-2 text-sm leading-6 text-slate-700">{topGap?.explanation || 'No active skill gap is currently available.'}</p><p className="mt-2 text-sm font-semibold text-navy">{topRecommendation ? `Recommended next: ${topRecommendation.title} · ${topRecommendation.source}` : 'Recommendation: Not provided'}</p></div></div></div></section>
}

function CompetencyHighlights({ title, detail, items, tone }: { title: string; detail: string; items: EmployeeCompetency[]; tone: 'teal' | 'amber' }) {
  return <div className="panel p-6"><div className="flex items-start gap-3"><span className={`status-icon ${tone === 'amber' ? 'bg-[#fff7e8] text-[#a86400]' : ''}`}>{tone === 'teal' ? <CheckCircle2 size={18} /> : <Target size={18} />}</span><div><h2 className="font-semibold text-navy">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div></div>{items.length ? <div className="mt-5 space-y-4">{items.map((item) => <div key={item.competency_id}><div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold text-navy">{item.name}</span><span className="text-sm font-bold text-teal">{item.current_score}%</span></div><div className="mt-2"><ScoreBar value={item.current_score} target={item.required_score} /></div><p className="mt-1 text-xs text-slate-500">Target {item.required_score}% · {item.current_level_label}</p></div>)}</div> : <div className="mt-5"><EmptyState title="No items in this view" detail="Complete an assessment to refine the profile." /></div>}</div>
}

function CompetencyRow({ item }: { item: EmployeeCompetency }) {
  return <div className="panel p-4 sm:p-5"><div className="flex flex-col gap-4 md:flex-row md:items-center"><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold text-navy">{item.name}</h3><LevelPill label={item.current_level_label} tone="teal" /><DeltaBadge delta={item.delta_from_previous} /></div><p className="mt-1 text-xs text-slate-500">{categoryLabels[item.category] || item.category} · target {item.target_level_label} ({item.required_score}%)</p></div><div className="w-full md:w-72"><div className="mb-2 flex justify-between text-xs"><span className="font-bold text-navy">{item.current_score}% current</span><span className="text-slate-500">{item.required_score}% target</span></div><ScoreBar value={item.current_score} target={item.required_score} /></div></div></div>
}
