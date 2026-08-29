import { useEffect, useState } from 'react'
import { Activity, BarChart3, Clock3, GraduationCap, Radio, RotateCcw, Target, TrendingUp, Users } from 'lucide-react'
import { AppShell } from '../components/AppShell'
import { ErrorState, LoadingState, PageHeader, ScoreBar } from '../components/Phase2UI'
import { api } from '../services/api'
import type { AdminDepartment, AdminOverview, BootstrapData, FutureDemand, TelemetryEvent } from '../types'

type AdminData = {
  overview: AdminOverview
  departments: AdminDepartment[]
  gaps: Record<string, unknown>[]
  training: Record<string, unknown>[]
  forecast: FutureDemand[]
  telemetry: Record<string, number>
  events: TelemetryEvent[]
}

export function AdminIntelligencePage() {
  const [data, setData] = useState<AdminData | null>(null)
  const [bootstrap, setBootstrap] = useState<BootstrapData | null>(null)
  const [error, setError] = useState('')
  const [resetting, setResetting] = useState(false)

  const load = async () => {
    setError('')
    try {
      const [overview, departments, gaps, training, forecast, telemetry, events] = await Promise.all([
        api.adminOverview(),
        api.adminDepartments(),
        api.adminGaps(),
        api.adminTraining(),
        api.adminForecast(),
        api.telemetrySummary(),
        api.recentTelemetryEvents(),
      ])
      setData({ overview, departments, gaps, training, forecast, telemetry, events })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load workforce intelligence')
    }
  }

  useEffect(() => {
    void load()
    api.bootstrap().then(setBootstrap).catch(() => undefined)
  }, [])

  const resetDemo = async () => {
    if (!bootstrap?.demo_mode || !window.confirm('Reset the synthetic demo to the clean Ananya Sharma baseline?')) return
    setResetting(true)
    setError('')
    try {
      await api.demoReset()
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reset the demo')
    } finally {
      setResetting(false)
    }
  }

  if (!data) {
    return <AppShell><PageHeader eyebrow="Administration · Intelligence" title="Workforce intelligence" description="Loading live organization aggregates from the competency and learning tables." />{error ? <ErrorState message={error} onRetry={() => void load()} /> : <LoadingState label="Aggregating workforce signals…" />}</AppShell>
  }

  const kpis = [
    [Users, 'Officials', data.overview.total_officials],
    [Target, 'Average competency', `${data.overview.average_competency}%`],
    [Activity, 'Critical skill gaps', data.overview.critical_skill_gaps],
    [GraduationCap, 'Completion rate', `${data.overview.training_completion_rate}%`],
    [Clock3, 'Learning hours', data.overview.learning_hours],
    [BarChart3, 'Assessment performance', `${data.overview.assessment_performance}%`],
  ] as const

  return <AppShell><div className="animate-rise">
    <PageHeader eyebrow="Administration · Server aggregates" title="Workforce intelligence" description="Organization readiness, department gaps, training effectiveness, and future demand calculated from persisted records—not UI constants." action={<div className="flex flex-wrap justify-end gap-2"><button type="button" className="secondary-button" onClick={() => void load()} disabled={resetting}>Refresh analytics</button>{bootstrap?.demo_mode && <button type="button" className="inline-flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm font-semibold text-amber-800 hover:border-amber-400 disabled:opacity-60" onClick={() => void resetDemo()} disabled={resetting}><RotateCcw size={15} />{resetting ? 'Resetting…' : 'Reset demo'}</button>}</div>} />
    {error && <div className="mt-6"><ErrorState message={error} onRetry={() => void load()} /></div>}
    <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{kpis.map(([Icon, label, value]) => <div className="panel flex items-center gap-3 p-5" key={label}><span className="status-icon"><Icon size={18} /></span><div><p className="text-2xl font-semibold text-navy">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div></div>)}</section>
    <section className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]"><div className="panel p-6"><p className="eyebrow text-teal">Department comparison</p><h2 className="mt-2 text-xl font-semibold text-navy">Readiness by department</h2><div className="mt-6 space-y-5">{data.departments.map((department) => <div key={department.department_id}><div className="flex items-center justify-between gap-3 text-sm"><span className="font-semibold text-navy">{department.department}</span><span className="font-bold text-teal">{department.average_competency}%</span></div><div className="mt-2"><ScoreBar value={department.average_competency} showTarget={false} /></div><div className="mt-1 flex justify-between text-xs text-slate-500"><span>{department.officials} officials · average gap {department.average_gap} pts</span><span>{department.critical_gaps} critical gaps</span></div></div>)}</div></div><div className="panel p-6"><div className="flex items-start gap-3"><span className="status-icon"><TrendingUp size={18} /></span><div><p className="eyebrow text-teal">Prototype forecast</p><h2 className="mt-2 text-xl font-semibold text-navy">Future skill demand</h2></div></div><p className="mt-3 text-xs leading-5 text-slate-500">Synthetic predictive analytics for demonstration; source and confidence are shown for every signal.</p><div className="mt-5 space-y-4">{data.forecast.slice(0, 7).map((item) => <div key={item.competency_id}><div className="flex items-center justify-between text-sm"><span className="font-semibold text-navy">{item.competency}</span><span className="font-bold text-teal">+{item.growth_rate}%</span></div><div className="mt-2 flex gap-2"><div className="h-2 flex-1 rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-300" style={{ width: `${item.current_demand}%` }} /></div><div className="h-2 flex-1 rounded-full bg-slate-100"><div className="h-full rounded-full bg-teal" style={{ width: `${item.projected_demand}%` }} /></div></div><p className="mt-1 text-[11px] text-slate-500">{item.current_demand}% now → {item.projected_demand}% projected · confidence {Math.round(item.confidence * 100)}%</p></div>)}</div></div></section>
    <section className="panel mt-6 p-6"><p className="eyebrow text-teal">Top organizational gaps</p><h2 className="mt-2 text-xl font-semibold text-navy">Where capacity-building should focus</h2><div className="mt-5 grid gap-3 md:grid-cols-2">{data.gaps.slice(0, 6).map((gap) => <div className="rounded-xl border border-line p-4" key={String(gap.competency_id)}><div className="flex justify-between gap-3"><p className="font-semibold text-navy">{String(gap.competency)}</p><span className="text-sm font-bold text-red-600">{String(gap.average_gap)} pts gap</span></div><p className="mt-1 text-xs text-slate-500">{String(gap.critical_count)} officials with critical signal · priority {String(gap.priority_score)}</p></div>)}</div></section>
    <section className="panel mt-6 overflow-hidden p-6"><div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-start gap-3"><span className="status-icon"><Radio size={18} /></span><div><p className="eyebrow text-teal">Sunbird-compatible prototype telemetry</p><h2 className="mt-2 text-xl font-semibold text-navy">Recent learner events</h2></div></div><p className="max-w-md text-xs leading-5 text-slate-500">Events are locally stored for demonstration and inspection; this is not a live Sunbird production connection.</p></div><div className="mt-5 grid gap-3 sm:grid-cols-4"><div className="rounded-xl bg-slate-50 p-3"><p className="text-lg font-semibold text-navy">{data.telemetry.learning_hours ?? 0}</p><p className="text-[11px] text-slate-500">Learning hours</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-lg font-semibold text-navy">{data.telemetry.assessment_accuracy ?? 0}%</p><p className="text-[11px] text-slate-500">Assessment accuracy</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-lg font-semibold text-navy">{data.telemetry.competency_improvement_rate ?? 0}</p><p className="text-[11px] text-slate-500">Average score delta</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-lg font-semibold text-navy">{data.events.length}</p><p className="text-[11px] text-slate-500">Recent events</p></div></div>{!data.events.length ? <p className="mt-5 rounded-xl border border-dashed border-line p-5 text-sm text-slate-500">No telemetry events yet. Run the trainer-to-learner demo to inspect the adaptive loop here.</p> : <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[720px] text-left text-xs"><thead className="border-b border-line text-[10px] uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-2">Event</th><th className="px-3 py-2">Actor</th><th className="px-3 py-2">Object</th><th className="px-3 py-2">Timestamp</th><th className="px-3 py-2">Message ID</th></tr></thead><tbody>{data.events.slice(0, 12).map((event) => <tr className="border-b border-line/70 last:border-0" key={event.mid}><td className="px-3 py-3 font-semibold text-teal">{event.eid}</td><td className="px-3 py-3 text-slate-600">{String(event.actor.id ?? 'authenticated user')}</td><td className="px-3 py-3 text-slate-600">{String(event.object.id ?? event.object.type ?? '—')}</td><td className="px-3 py-3 text-slate-600">{new Date(event.ets).toLocaleString()}</td><td className="max-w-[220px] truncate px-3 py-3 font-mono text-[10px] text-slate-500">{event.mid}</td></tr>)}</tbody></table></div>}</section>
  </div></AppShell>
}
