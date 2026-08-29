import { useEffect, useState, type ReactNode } from 'react'
import { Activity, ArrowRight, BarChart3, BookOpen, BrainCircuit, CheckCircle2, ChevronRight, CircleUserRound, Database, FileText, GraduationCap, LayoutDashboard, LogOut, Menu, Network, ShieldCheck, Sparkles, Target, X } from 'lucide-react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLanguage, type TranslationKey } from '../i18n'
import { api } from '../services/api'
import type { BootstrapData, Role } from '../types'

const roleMeta: Record<Role, { label: string; eyebrow: string }> = {
  EMPLOYEE: { label: 'Employee workspace', eyebrow: 'Official learning' },
  ADMIN: { label: 'Administration workspace', eyebrow: 'Workforce intelligence' },
  TRAINER: { label: 'Trainer workspace', eyebrow: 'Assessment authoring' },
}

const employeeNav: { key: TranslationKey; href: string; icon: typeof LayoutDashboard }[] = [
  { key: 'dashboard', href: '/employee/dashboard', icon: LayoutDashboard },
  { key: 'myProfile', href: '/employee/profile', icon: CircleUserRound },
  { key: 'myCompetencies', href: '/employee/competencies', icon: Target },
  { key: 'fracIntelligence', href: '/employee/intelligence', icon: Network },
  { key: 'assessment', href: '/employee/assessment', icon: CheckCircle2 },
  { key: 'skillGaps', href: '/employee/skill-gaps', icon: Activity },
  { key: 'learningPath', href: '/employee/learning-path', icon: BookOpen },
  { key: 'quiz', href: '/employee/quiz', icon: GraduationCap },
  { key: 'statbot', href: '/employee/assistant', icon: BrainCircuit },
]

const trainerNav = [
  { label: 'Workspace home', href: '/trainer/dashboard', icon: LayoutDashboard },
  { label: 'AI Assessment Studio', href: '/trainer/assessment-studio', icon: Sparkles },
]

const laterNav = [
  { label: 'AI Assessment Studio', icon: Sparkles },
  { label: 'StatBot assistant', icon: BrainCircuit },
]

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth()
  const { language, setLanguage, t } = useLanguage()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [bootstrap, setBootstrap] = useState<BootstrapData | null>(null)
  const location = useLocation()
  const meta = user ? roleMeta[user.role] : roleMeta.EMPLOYEE

  useEffect(() => { api.bootstrap().then(setBootstrap).catch(() => undefined) }, [])
  if (!user) return null
  const homePath = `/${user.role.toLowerCase()}/dashboard`

  return <div className="min-h-screen bg-mist text-ink">
    <header className="sticky top-0 z-30 border-b border-line bg-white/95 backdrop-blur-sm"><div className="mx-auto flex h-20 max-w-[1440px] items-center justify-between px-4 sm:px-6 lg:px-8"><div className="flex items-center gap-3"><button className="icon-button lg:hidden" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu size={20} /></button><Link to={homePath} className="flex items-center gap-3" aria-label="AI STAT-GROWTH home"><span className="grid h-10 w-10 place-items-center rounded-xl bg-navy text-white shadow-soft"><BarChart3 size={21} /></span><span className="hidden sm:block"><span className="block text-sm font-bold tracking-[0.14em] text-navy">AI STAT-GROWTH</span><span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Competency intelligence</span></span></Link></div><div className="flex items-center gap-3"><div className="hidden text-right sm:block"><p className="text-sm font-semibold text-ink">{user.full_name}</p><p className="text-xs text-slate-500">{user.designation} · {user.department}</p></div>{user.role === 'EMPLOYEE' && <label className="flex items-center gap-2"><span className="sr-only">{t('language')}</span><select aria-label={t('language')} className="rounded-lg border border-line bg-white px-2.5 py-2 text-xs font-semibold text-navy outline-none focus:border-teal focus:ring-2 focus:ring-teal/20" value={language} onChange={(event) => setLanguage(event.target.value as 'en' | 'hi')}><option value="en">{t('english')}</option><option value="hi">{t('hindi')}</option></select></label>}<div className="avatar" title={user.full_name}>{user.full_name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</div></div></div></header>
    <div className="mx-auto flex max-w-[1440px]">{mobileOpen && <button className="fixed inset-0 z-30 bg-navy/25 lg:hidden" aria-label="Close navigation overlay" onClick={() => setMobileOpen(false)} />}<aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}><div className="flex items-center justify-between border-b border-line pb-5 lg:hidden"><p className="font-bold text-navy">Navigation</p><button className="icon-button" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X size={18} /></button></div><div className="mb-7 rounded-2xl bg-[#eef7f6] p-4"><p className="eyebrow text-teal">{meta.eyebrow}</p><p className="mt-1 text-sm font-semibold text-navy">{meta.label}</p><p className="mt-2 text-xs leading-5 text-slate-600">A secure starting point for the adaptive learning loop.</p></div><nav aria-label="Primary navigation"><p className="eyebrow mb-3 px-3">{t('workspace')}</p>{user.role === 'EMPLOYEE' ? employeeNav.map(({ key, href, icon: Icon }) => <NavLink end={href.endsWith('dashboard')} to={href} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`} key={href}><Icon size={17} /><span>{t(key)}</span></NavLink>) : user.role === 'TRAINER' ? trainerNav.map(({ label, href, icon: Icon }) => <NavLink end={href.endsWith('dashboard')} to={href} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`} key={href}><Icon size={17} /><span>{label}</span></NavLink>) : <NavLink end to={homePath} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}><LayoutDashboard size={17} />{t('dashboard')}</NavLink>}<div className="mt-7"><p className="eyebrow mb-3 px-3">{user.role === 'EMPLOYEE' ? t('comingNext') : t('plannedModules')}</p>{laterNav.filter((item) => !((user.role === 'TRAINER' && item.label === 'AI Assessment Studio') || (user.role === 'EMPLOYEE' && item.label === 'StatBot assistant'))).map(({ label, icon: Icon }) => <div className="nav-link nav-link-disabled" key={label} title="Planned for a later vertical slice"><Icon size={17} /><span>{label}</span><span className="ml-auto text-[9px] font-bold uppercase tracking-wider text-slate-400">{t('next')}</span></div>)}</div></nav><div className="mt-auto border-t border-line pt-5"><button className="nav-link w-full text-slate-600 hover:bg-red-50 hover:text-red-700" onClick={signOut}><LogOut size={17} />Sign out</button></div></aside><main className="min-w-0 flex-1 px-4 py-7 sm:px-6 lg:px-10 lg:py-10"><div className="mx-auto max-w-6xl">{children}</div><footer className="mx-auto mt-14 flex max-w-6xl flex-col gap-2 border-t border-line pt-5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between"><span>AI STAT-GROWTH · SIH competition-ready prototype</span><span className="flex items-center gap-1.5"><ShieldCheck size={14} className="text-teal" /> Synthetic demo data · No live government integrations</span></footer></main></div>{bootstrap && location.pathname.endsWith('/dashboard') && <div className="sr-only">{bootstrap.seeded_counts.users} seeded users</div>}</div>
}

export function StatusIcon({ type }: { type: 'database' | 'security' | 'api' | 'ai' }) {
  const icons = { database: Database, security: ShieldCheck, api: Network, ai: BrainCircuit }
  const Icon = icons[type]
  return <span className="status-icon"><Icon size={17} /></span>
}

export function ShellLink({ label, href }: { label: string; href: string }) {
  return <Link to={href} className="inline-flex items-center gap-1.5 text-sm font-semibold text-teal hover:text-navy">{label}<ArrowRight size={15} /></Link>
}
