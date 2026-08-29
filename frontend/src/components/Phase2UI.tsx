import type { LucideIcon } from 'lucide-react'
import { AlertCircle, CheckCircle2, LoaderCircle, RefreshCw, TrendingUp } from 'lucide-react'
import type { EmployeeCompetency, GapSeverity } from '../types'

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: React.ReactNode }) {
  return <div className="flex flex-col justify-between gap-5 border-b border-line pb-7 md:flex-row md:items-end">
    <div><p className="eyebrow text-teal">{eyebrow}</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-navy sm:text-4xl">{title}</h1>{description && <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>}</div>
    {action && <div className="shrink-0">{action}</div>}
  </div>
}

export function LoadingState({ label = 'Loading your capability data…' }: { label?: string }) {
  return <div className="panel flex min-h-56 items-center justify-center p-8"><div className="flex items-center gap-3 text-sm text-slate-600"><LoaderCircle className="animate-spin text-teal" size={20} />{label}</div></div>
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800" role="alert"><div className="flex items-start gap-3"><AlertCircle className="mt-0.5 shrink-0" size={19} /><div className="min-w-0 flex-1"><p className="font-semibold">We could not load this view</p><p className="mt-1 text-sm leading-6 text-red-700">{message}</p><button type="button" className="mt-4 inline-flex items-center gap-2 rounded-lg border border-red-300 bg-white px-3 py-2 text-xs font-semibold text-red-800 hover:bg-red-100" onClick={onRetry}><RefreshCw size={14} />Retry</button></div></div></div>
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="panel flex min-h-44 items-center justify-center p-8 text-center"><div><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-[#eef7f6] text-teal"><CheckCircle2 size={19} /></div><h3 className="mt-4 font-semibold text-navy">{title}</h3><p className="mt-1 text-sm text-slate-500">{detail}</p></div></div>
}

export function MetricCard({ icon: Icon, label, value, caption, tone = 'navy' }: { icon: LucideIcon; label: string; value: string | number; caption: string; tone?: 'navy' | 'teal' | 'blue' | 'amber' }) {
  return <div className="panel p-5"><div className="flex items-start justify-between gap-3"><span className={`metric-icon metric-${tone}`}><Icon size={18} /></span><TrendingUp size={15} className="text-slate-300" /></div><p className="mt-5 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">{label}</p><p className="mt-1 text-2xl font-semibold tracking-tight text-navy">{value}</p><p className="mt-1 text-xs text-slate-500">{caption}</p></div>
}

export function ScoreBar({ value, target, showTarget = true, color = 'teal' }: { value: number; target?: number; showTarget?: boolean; color?: 'teal' | 'navy' | 'amber' }) {
  const safeValue = Math.max(0, Math.min(100, value))
  const safeTarget = target === undefined ? undefined : Math.max(0, Math.min(100, target))
  return <div className="relative pt-1"><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full transition-all duration-500 ${color === 'navy' ? 'bg-navy' : color === 'amber' ? 'bg-amber-500' : 'bg-teal'}`} style={{ width: `${safeValue}%` }} /></div>{showTarget && safeTarget !== undefined && <span className="absolute -top-0.5 h-4 w-px bg-navy/50" style={{ left: `calc(${safeTarget}% - 1px)` }} title={`Target ${safeTarget}%`} />}</div>
}

export function SeverityBadge({ severity }: { severity: GapSeverity }) {
  const labels: Record<GapSeverity, string> = { critical: 'Critical', high: 'High priority', medium: 'Medium', low: 'Low' }
  const colors: Record<GapSeverity, string> = { critical: 'border-red-200 bg-red-50 text-red-700', high: 'border-orange-200 bg-orange-50 text-orange-700', medium: 'border-amber-200 bg-amber-50 text-amber-700', low: 'border-slate-200 bg-slate-50 text-slate-600' }
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-bold ${colors[severity]}`}>{labels[severity]}</span>
}

export function LevelPill({ label, tone = 'slate' }: { label: string; tone?: 'teal' | 'slate' }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${tone === 'teal' ? 'bg-[#e8f5f2] text-teal' : 'bg-slate-100 text-slate-600'}`}>{label}</span>
}

export function initials(name: string) {
  return name.split(' ').filter(Boolean).map((part) => part[0]).slice(0, 2).join('').toUpperCase()
}

export function formatCategory(category: string) {
  return category.replace(' & ', ' and ')
}

export function RadarChart({ values, size = 300 }: { values: Record<string, number>; size?: number }) {
  const entries = Object.entries(values)
  if (entries.length === 0) return <EmptyState title="No category data yet" detail="Complete an assessment to populate this chart." />
  const center = size / 2
  const radius = size * 0.33
  const angle = (index: number) => -Math.PI / 2 + (index * Math.PI * 2) / entries.length
  const point = (value: number, index: number) => {
    const ratio = Math.max(0, Math.min(100, value)) / 100
    return `${center + Math.cos(angle(index)) * radius * ratio},${center + Math.sin(angle(index)) * radius * ratio}`
  }
  const outer = entries.map((_, index) => point(100, index)).join(' ')
  const middle = entries.map((_, index) => point(50, index)).join(' ')
  const data = entries.map(([_, value], index) => point(value, index)).join(' ')
  return <div className="flex min-w-0 flex-col items-center"><svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Competency category radar chart" className="max-w-full overflow-visible">
    <polygon points={outer} fill="none" stroke="#d9e2ec" strokeWidth="1" /><polygon points={middle} fill="none" stroke="#e7edf2" strokeWidth="1" />
    {entries.map(([label], index) => { const x = center + Math.cos(angle(index)) * radius; const y = center + Math.sin(angle(index)) * radius; return <g key={label}><line x1={center} y1={center} x2={x} y2={y} stroke="#e7edf2" strokeWidth="1" /><text x={center + Math.cos(angle(index)) * (radius + 22)} y={center + Math.sin(angle(index)) * (radius + 22)} textAnchor="middle" dominantBaseline="middle" fontSize="10" fill="#52606d">{label.length > 17 ? `${label.slice(0, 15)}…` : label}</text></g> })}
    <polygon points={data} fill="#0f766e" fillOpacity="0.16" stroke="#0f766e" strokeWidth="2.5" />
    {entries.map(([label, value], index) => { const [x, y] = point(value, index).split(','); return <circle key={label} cx={x} cy={y} r="3.5" fill="#0f766e" stroke="white" strokeWidth="2" /> })}
  </svg><div className="mt-1 flex flex-wrap justify-center gap-x-4 gap-y-2 text-[11px] text-slate-500">{entries.map(([label, value]) => <span key={label}><span className="font-semibold text-navy">{value}%</span> {formatCategory(label)}</span>)}</div></div>
}

export function DeltaBadge({ delta }: { delta: number | null | undefined }) {
  if (delta === null || delta === undefined || delta === 0) return null
  return <span className={`rounded-full px-2 py-1 text-[11px] font-bold ${delta > 0 ? 'bg-[#e8f5f2] text-teal' : 'bg-red-50 text-red-700'}`}>{delta > 0 ? '+' : ''}{delta} pts</span>
}

export function competencyTargetText(item: EmployeeCompetency) {
  return `${item.current_level_label} → ${item.target_level_label}`
}
