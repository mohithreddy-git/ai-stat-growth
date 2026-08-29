import { AlertTriangle, ArrowRight, BarChart3, CheckCircle2, ChevronRight, Flag, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { AppShell } from '../components/AppShell'
import { EmptyState, ErrorState, LoadingState, PageHeader, ScoreBar, SeverityBadge } from '../components/Phase2UI'
import { api } from '../services/api'
import type { SkillGap } from '../types'

const severityOrder = ['critical', 'high', 'medium', 'low'] as const

export function EmployeeSkillGapsPage() {
  const { user } = useAuth()
  const [gaps, setGaps] = useState<SkillGap[] | null>(null)
  const [error, setError] = useState('')
  const load = () => { if (!user) return; setError(''); api.skillGaps(user.id).then(setGaps).catch((err) => setError(err instanceof Error ? err.message : 'Unable to calculate skill gaps')) }
  useEffect(load, [user?.id])
  return <AppShell><div className="animate-rise"><PageHeader eyebrow="Gap analysis · Step 03" title="Prioritised skill gaps" description="The engine compares current competency with role targets, then weighs role relevance, department priorities, future demand, and learning history." action={<Link className="primary-button" to="/employee/learning-path">See learning path <ArrowRight size={16} /></Link>} />
    <div className="mt-8">{error ? <ErrorState message={error} onRetry={load} /> : !gaps ? <LoadingState label="Calculating prioritised gaps…" /> : <GapContent gaps={gaps} />}</div>
  </div></AppShell>
}

function GapContent({ gaps }: { gaps: SkillGap[] }) {
  const critical = gaps.filter((gap) => gap.severity === 'critical')
  const high = gaps.filter((gap) => gap.severity === 'high')
  const largest = gaps.filter((gap) => gap.gap > 0).slice(0, 3)
  const averageGap = gaps.length ? Math.round(gaps.reduce((total, item) => total + item.gap, 0) / gaps.length) : 0
  return <>
    <section className="grid gap-4 sm:grid-cols-3"><SummaryCard icon={AlertTriangle} label="Critical gaps" value={critical.length} detail="Need immediate learning action" tone="red" /><SummaryCard icon={Flag} label="High priority" value={high.length} detail="Role-relevant development focus" tone="amber" /><SummaryCard icon={BarChart3} label="Average gap" value={`${averageGap} pts`} detail="Across the mapped framework" tone="teal" /></section>
    {largest.length ? <section className="mt-8"><div className="mb-4 flex items-end justify-between gap-4"><div><p className="eyebrow text-red-600">Action now</p><h2 className="mt-2 text-xl font-semibold text-navy">Largest capability gaps</h2></div><p className="hidden text-xs text-slate-500 sm:block">Ranked by the server-side priority score</p></div><div className="grid gap-4 lg:grid-cols-3">{largest.map((gap) => <PriorityCard gap={gap} key={gap.competency_id} />)}</div></section> : <div className="mt-8"><EmptyState title="No current skill gaps" detail="Your profile meets every seeded role target." /></div>}
    <section className="mt-8"><div className="mb-4"><p className="eyebrow text-teal">Evidence behind the ranking</p><h2 className="mt-2 text-xl font-semibold text-navy">All competencies compared with target</h2></div><div className="panel overflow-hidden"><div className="hidden grid-cols-[1.2fr_0.8fr_0.55fr_0.7fr_1.5fr] gap-4 border-b border-line bg-slate-50 px-5 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 md:grid"><span>Competency</span><span>Current → target</span><span>Gap</span><span>Priority</span><span>Reason</span></div><div className="divide-y divide-line">{gaps.map((gap) => <GapRow gap={gap} key={gap.competency_id} />)}</div></div></section>
  </>
}

function SummaryCard({ icon: Icon, label, value, detail, tone }: { icon: typeof Target; label: string; value: string | number; detail: string; tone: 'red' | 'amber' | 'teal' }) {
  const styles = { red: 'bg-red-50 text-red-700', amber: 'bg-[#fff7e8] text-[#a86400]', teal: 'bg-[#e8f5f2] text-teal' }
  return <div className="panel p-5"><span className={`metric-icon ${styles[tone]}`}><Icon size={18} /></span><p className="mt-5 text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-1 text-2xl font-semibold text-navy">{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></div>
}

function PriorityCard({ gap }: { gap: SkillGap }) {
  return <div className="panel border-l-4 border-l-red-500 p-5"><div className="flex items-start justify-between gap-3"><div><p className="eyebrow text-red-600">{gap.category}</p><h3 className="mt-2 text-lg font-semibold text-navy">{gap.competency}</h3></div><SeverityBadge severity={gap.severity} /></div><div className="mt-6 flex items-end justify-between"><div><p className="text-3xl font-semibold tracking-tight text-navy">{gap.current_score}%</p><p className="mt-1 text-xs text-slate-500">Current competency</p></div><div className="text-right"><p className="text-lg font-semibold text-red-600">−{gap.gap} pts</p><p className="mt-1 text-xs text-slate-500">Target {gap.required_score}%</p></div></div><div className="mt-4"><ScoreBar value={gap.current_score} target={gap.required_score} color="amber" /></div><div className="mt-5 border-t border-line pt-4"><p className="text-xs font-semibold leading-5 text-slate-600">{gap.explanation}</p><Link to="/employee/learning-path" className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-teal hover:text-navy">Recommended next action <ChevronRight size={14} /></Link></div></div>
}

function GapRow({ gap }: { gap: SkillGap }) {
  return <div className="grid gap-4 px-5 py-5 md:grid-cols-[1.2fr_0.8fr_0.55fr_0.7fr_1.5fr] md:items-center"><div><div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-teal" /><p className="font-semibold text-navy">{gap.competency}</p></div><p className="mt-1 pl-4 text-xs text-slate-500">{gap.category}</p></div><div><p className="text-sm font-semibold text-navy">{gap.current_score}% <span className="font-normal text-slate-400">→ {gap.required_score}%</span></p><div className="mt-2"><ScoreBar value={gap.current_score} target={gap.required_score} /></div></div><p className={`text-sm font-bold ${gap.gap >= 30 ? 'text-red-600' : gap.gap >= 20 ? 'text-orange-600' : 'text-slate-700'}`}>{gap.gap} pts</p><div><SeverityBadge severity={gap.severity} /><p className="mt-1 text-xs text-slate-500">Score {gap.priority_score}</p></div><div><p className="text-sm leading-6 text-slate-600">{gap.explanation}</p><p className="mt-2 text-xs font-semibold text-teal">{gap.recommended_next_action}</p></div></div>
}
