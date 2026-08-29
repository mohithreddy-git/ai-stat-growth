import { ArrowUpRight, BookOpen, CheckCircle2, Clock3, ExternalLink, Flag, PlayCircle, RotateCw, Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../i18n'
import { AppShell } from '../components/AppShell'
import { EmptyState, ErrorState, LoadingState, PageHeader, ScoreBar, SeverityBadge } from '../components/Phase2UI'
import { api } from '../services/api'
import type { LearningProgress, LearningResource, ProgressStatus, ResourceType } from '../types'

export function EmployeeLearningPathPage() {
  const { user } = useAuth()
  const { language, t } = useLanguage()
  const [resources, setResources] = useState<LearningResource[] | null>(null)
  const [progress, setProgress] = useState<LearningProgress[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState<string | null>(null)

  const load = async () => {
    if (!user) return
    setError('')
    try {
      const [recommendations, progressRows] = await Promise.all([api.recommendations(user.id, language), api.learningProgress(user.id)])
      setResources(recommendations)
      setProgress(progressRows)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your learning path')
    }
  }
  useEffect(() => { void load() }, [user?.id, language])

  const saveProgress = async (resource: LearningResource) => {
    if (!user) return
    const key = `${resource.resource_type}-${resource.id}`
    const existing = progress.find((item) => item.resource_type === resource.resource_type && item.resource_id === resource.id)
    const current = existing?.completion_percent ?? resource.completion_percent
    const next: { status: ProgressStatus; completion_percent: number; learning_hours: number } = current >= 100
      ? { status: 'completed', completion_percent: 100, learning_hours: resource.duration }
      : existing?.status === 'in_progress'
        ? { status: 'completed', completion_percent: 100, learning_hours: resource.duration }
        : { status: 'in_progress', completion_percent: Math.max(25, Math.min(90, current + 25)), learning_hours: Math.max(0.5, Math.round(resource.duration * Math.max(25, current + 25) / 100 * 10) / 10) }
    setBusy(key)
    setError('')
    try {
      await api.saveLearningProgress(user.id, { resource_type: resource.resource_type, resource_id: resource.id, ...next })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save learning progress')
    } finally {
      setBusy(null)
    }
  }

  return <AppShell><div className="animate-rise"><PageHeader eyebrow="Personalised pathway · Step 04" title={t('learningPath')} description="Recommendations are ranked from the current gap engine. Each source is clearly labelled as a prototype dataset until an approved government integration is connected." action={<button type="button" className="icon-button border border-line bg-white" onClick={() => void load()} aria-label={`${t('learningPath')} refresh`}><RotateCw size={17} /></button>} />
    <div className="mt-8">{error && <div className="mb-6"><ErrorState message={error} onRetry={() => void load()} /></div>}{!resources ? <LoadingState label="Ranking learning resources for your gaps…" /> : resources.length === 0 ? <EmptyState title="No learning recommendations yet" detail="Your current profile has no open gaps that need a learning resource." /> : <PathContent resources={resources} progress={progress} onAction={saveProgress} busy={busy} />}</div>
  </div></AppShell>
}

function PathContent({ resources, progress, onAction, busy }: { resources: LearningResource[]; progress: LearningProgress[]; onAction: (resource: LearningResource) => void; busy: string | null }) {
  const { t } = useLanguage()
  const groups = useMemo(() => {
    const critical = resources.filter((resource) => resource.priority === 'critical')
    const next = resources.filter((resource) => resource.priority === 'high' || resource.priority === 'medium')
    const optional = resources.filter((resource) => resource.priority === 'low')
    return [{ label: 'Top priority', detail: 'Close the largest capability gaps first.', resources: critical }, { label: 'Next best learning', detail: 'Build adjacent capability for role readiness.', resources: next }, { label: 'Optional / development', detail: 'Useful growth areas after urgent gaps are addressed.', resources: optional }]
  }, [resources])
  const completed = progress.filter((item) => item.status === 'completed').length
  return <>
    <section className="grid gap-4 sm:grid-cols-3"><div className="panel border-l-4 border-l-red-500 p-5"><p className="eyebrow text-red-600">{t('skillGaps')}</p><p className="mt-2 text-2xl font-semibold text-navy">{groups[0].resources.length}</p><p className="mt-1 text-xs text-slate-500">{t('recommendations')}</p></div><div className="panel p-5"><p className="eyebrow text-teal">{t('recommendations')}</p><p className="mt-2 text-2xl font-semibold text-navy">{resources.length}</p><p className="mt-1 text-xs text-slate-500">Across iGOT and NSSTA / TPAC sources</p></div><div className="panel p-5"><p className="eyebrow text-teal">{t('progress')}</p><p className="mt-2 text-2xl font-semibold text-navy">{completed}</p><p className="mt-1 text-xs text-slate-500">Recommended resources completed</p></div></section>
    <div className="mt-9 space-y-10">{groups.map((group) => group.resources.length ? <section key={group.label}><div className="mb-4"><p className="eyebrow text-teal">{group.label}</p><h2 className="mt-2 text-xl font-semibold text-navy">{group.detail}</h2></div><div className="grid gap-5 lg:grid-cols-2">{group.resources.map((resource) => <RecommendationCard key={`${resource.resource_type}-${resource.id}`} resource={resource} progress={progress.find((item) => item.resource_type === resource.resource_type && item.resource_id === resource.id)} onAction={onAction} busy={busy === `${resource.resource_type}-${resource.id}`} />)}</div></section> : null)}</div>
  </>
}

function RecommendationCard({ resource, progress, onAction, busy }: { resource: LearningResource; progress?: LearningProgress; onAction: (resource: LearningResource) => void; busy: boolean }) {
  const { t } = useLanguage()
  const percent = progress?.completion_percent ?? resource.completion_percent
  const status = progress?.status ?? resource.progress_status
  const statusLabel = status === 'completed' ? t('completed') : status === 'in_progress' ? t('inProgress') : t('notStarted')
  const isProgramme = resource.resource_type === 'training_programme'
  return <article className="panel overflow-hidden transition hover:-translate-y-0.5 hover:shadow-soft"><div className="border-b border-line p-5 sm:p-6"><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 items-start gap-3"><span className={`status-icon shrink-0 ${isProgramme ? 'bg-[#eef2ff] text-[#4653a5]' : ''}`}>{isProgramme ? <Flag size={18} /> : <BookOpen size={18} />}</span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold leading-6 text-navy">{resource.title}</h3><SeverityBadge severity={resource.priority} /></div><p className="mt-1 text-xs font-semibold text-teal">{resource.source} · {resource.competency}</p></div></div><div className="shrink-0 text-right"><p className="text-xl font-semibold text-navy">{resource.relevance_score}</p><p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">relevance</p></div></div><p className="mt-5 text-sm leading-6 text-slate-600">{resource.description}</p><div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500"><span className="inline-flex items-center gap-1.5"><Clock3 size={14} />{resource.duration_label}</span><span className="inline-flex items-center gap-1.5"><Sparkles size={14} />{resource.difficulty}</span><span className="rounded-full bg-slate-100 px-2 py-1 font-semibold">{isProgramme ? 'Training programme' : 'Course'}</span></div></div><div className="bg-slate-50/70 p-5 sm:p-6"><div className="flex items-center justify-between gap-4 text-xs"><span className="font-bold text-navy">{statusLabel}</span><span className="font-semibold text-slate-500">{percent}%</span></div><div className="mt-2"><ScoreBar value={percent} showTarget={false} /></div><div className="mt-5 rounded-xl border border-teal/20 bg-white p-4"><p className="text-xs font-bold text-navy">{t('whyRecommendation')}</p><p className="mt-2 text-xs leading-5 text-slate-600">{resource.reason}</p><div className="mt-3 grid gap-2 text-[11px] sm:grid-cols-3"><span>Current <strong className="text-navy">{resource.current_score}%</strong></span><span>Target <strong className="text-navy">{resource.required_score}%</strong></span><span>Expected +<strong className="text-teal">{resource.expected_improvement} pts</strong></span></div></div><div className="mt-4 flex flex-wrap items-center justify-between gap-3"><button type="button" className="primary-button px-4 py-2.5 text-xs" onClick={() => onAction(resource)} disabled={busy || status === 'completed'}>{busy ? `${t('progress')}…` : status === 'not_started' ? <><PlayCircle size={15} />{t('startLearning')}</> : <><CheckCircle2 size={15} />{t('markComplete')}</>}</button><a className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-teal" href={resource.url} target="_blank" rel="noreferrer">Resource reference <ExternalLink size={13} /></a></div></div></article>
}
