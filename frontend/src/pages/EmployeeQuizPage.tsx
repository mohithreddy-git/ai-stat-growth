import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, CheckCircle2, ClipboardCheck, RotateCcw, Target, XCircle } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useLanguage } from '../i18n'
import { AppShell } from '../components/AppShell'
import { EmptyState, ErrorState, LoadingState, PageHeader, ScoreBar } from '../components/Phase2UI'
import { api } from '../services/api'
import type { CompetencyProfile, LearningResource, PublishedQuizDetails, QuizResult } from '../types'

export function EmployeeQuizPage() {
  const { user } = useAuth()
  const { language, t } = useLanguage()
  const [searchParams, setSearchParams] = useSearchParams()
  const [quizIdInput, setQuizIdInput] = useState(searchParams.get('quizId') || '')
  const [quiz, setQuiz] = useState<PublishedQuizDetails | null>(null)
  const [beforeProfile, setBeforeProfile] = useState<CompetencyProfile | null>(null)
  const [afterProfile, setAfterProfile] = useState<CompetencyProfile | null>(null)
  const [beforeRecommendations, setBeforeRecommendations] = useState<LearningResource[]>([])
  const [afterRecommendations, setAfterRecommendations] = useState<LearningResource[]>([])
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [result, setResult] = useState<QuizResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadQuiz = async (value = quizIdInput) => {
    if (!user || !value || !Number.isInteger(Number(value)) || Number(value) < 1) {
      setError('Enter a valid published quiz ID.')
      return
    }
    setBusy(true)
    setError('')
    setResult(null)
    setAnswers({})
    setCurrentIndex(0)
    try {
      const id = Number(value)
      const [loadedQuiz, profile, recommendations] = await Promise.all([api.getQuiz(id, language), api.competencies(user.id), api.recommendations(user.id, language)])
      setQuiz(loadedQuiz)
      setBeforeProfile(profile)
      setAfterProfile(null)
      setBeforeRecommendations(recommendations)
      setAfterRecommendations([])
      setSearchParams({ quizId: String(id) })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this published quiz')
      setQuiz(null)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    const initialId = searchParams.get('quizId')
    if (initialId && user) void loadQuiz(initialId)
    // The URL is the explicit quiz selection; do not reload on every state update.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id])

  useEffect(() => {
    if (!quiz || !user || result) return
    api.getQuiz(quiz.id, language).then(setQuiz).catch(() => undefined)
  }, [language])

  const currentQuestion = quiz?.items[currentIndex]
  const answeredCount = quiz ? Object.keys(answers).length : 0
  const allAnswered = !!quiz && answeredCount === quiz.items.length

  const updates = useMemo(() => {
    if (!result || !beforeProfile) return []
    const beforeById = new Map(beforeProfile.competencies.map((item) => [item.competency_id, item]))
    const seen = new Set<number>()
    return result.explanations.map((item) => item.item_id).map((itemId) => quiz?.items.find((item) => item.id === itemId)).filter((item): item is NonNullable<typeof item> => {
      if (!item || seen.has(item.competency_id)) return false
      seen.add(item.competency_id)
      return true
    }).map((item) => {
      const before = beforeById.get(item.competency_id)
      const after = afterProfile?.competencies.find((candidate) => candidate.competency_id === item.competency_id)
      return { competency: before?.name || `Competency #${item.competency_id}`, before: before?.current_score || 0, after: after?.current_score || before?.current_score || 0, target: before?.required_score || 0 }
    })
  }, [afterProfile, beforeProfile, quiz, result])

  const submit = async () => {
    if (!user || !quiz || !allAnswered) return
    setBusy(true)
    setError('')
    try {
      const submitted = await api.submitQuiz(quiz.id, answers, language)
      const [updatedProfile, updatedRecommendations] = await Promise.all([api.competencies(user.id), api.recommendations(user.id, language)])
      setResult(submitted)
      setAfterProfile(updatedProfile)
      setAfterRecommendations(updatedRecommendations)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Quiz submission failed. Your answers were not scored.')
    } finally {
      setBusy(false)
    }
  }

  if (!quiz) {
    return <AppShell><div className="animate-rise"><PageHeader eyebrow={`Learner workspace · ${t('assessment')}`} title={t('quiz')} description="Open a published trainer quiz by ID. Correct answers remain hidden until the server evaluates your submission." />{error && <div className="mt-6"><ErrorState message={error} onRetry={() => setError('')} /></div>}<section className="panel mt-8 max-w-xl p-6 sm:p-8"><div className="flex items-start gap-3"><span className="status-icon"><ClipboardCheck size={18} /></span><div><p className="eyebrow text-teal">{t('quiz')}</p><h2 className="mt-2 text-xl font-semibold text-navy">{language === 'hi' ? 'क्विज़ आईडी दर्ज करें' : 'Enter quiz ID'}</h2></div></div><label className="mt-6 block"><span className="text-xs font-bold uppercase tracking-wide text-slate-500">Quiz ID</span><input className="form-input mt-2" inputMode="numeric" value={quizIdInput} onChange={(event) => setQuizIdInput(event.target.value)} placeholder="Example: 1" /></label><button type="button" className="primary-button mt-5" disabled={busy} onClick={() => void loadQuiz()}>{busy ? t('loading') : language === 'hi' ? 'क्विज़ खोलें' : 'Open quiz'}<ArrowRight size={16} /></button></section></div></AppShell>
  }

  if (!currentQuestion) return <AppShell><EmptyState title="This quiz has no available items" detail="Ask the trainer to publish a valid quiz." /></AppShell>

  return <AppShell><div className="animate-rise"><PageHeader eyebrow={`Learner workspace · ${t('quiz')}`} title={quiz.title} description="Answer every question before submitting. The backend evaluates responses and updates only the competency evidence supported by this quiz." action={<Link className="secondary-button" to="/employee/learning-path"><Target size={16} />{t('learningPath')}</Link>} />
    {!result ? <section className="panel mt-8 max-w-4xl p-6 sm:p-8"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="eyebrow text-teal">{t('quiz')} · {currentIndex + 1} / {quiz.items.length}</p><h2 className="mt-2 text-xl font-semibold text-navy">{currentQuestion.question}</h2></div><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600">{currentQuestion.difficulty}</span>{language === 'hi' && <span className="rounded-full bg-[#eef7f6] px-3 py-1.5 text-xs font-semibold text-teal">{currentQuestion.localized ? t('prototypeMultilingual') : t('notAvailable')}</span>}</div></div><div className="mt-5"><div className="flex justify-between text-xs text-slate-500"><span>{answeredCount} {t('answered')}</span><span>{Math.round((answeredCount / quiz.items.length) * 100)}% {t('progress')}</span></div><div className="mt-2"><ScoreBar value={(answeredCount / quiz.items.length) * 100} showTarget={false} /></div></div><div className="mt-7 space-y-3">{currentQuestion.options.map((option, index) => <button type="button" key={option} onClick={() => setAnswers((current) => ({ ...current, [currentQuestion.id]: index }))} className={`flex w-full items-start gap-3 rounded-xl border p-4 text-left text-sm transition ${answers[currentQuestion.id] === index ? 'border-teal bg-[#eef7f6] text-navy ring-2 ring-teal/20' : 'border-line bg-white text-slate-700 hover:border-teal/50'}`}><span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-bold ${answers[currentQuestion.id] === index ? 'bg-teal text-white' : 'bg-slate-100 text-slate-500'}`}>{String.fromCharCode(65 + index)}</span><span>{option}</span></button>)}</div><div className="mt-8 flex flex-wrap justify-between gap-3 border-t border-line pt-5"><button type="button" className="secondary-button" disabled={currentIndex === 0} onClick={() => setCurrentIndex((index) => index - 1)}><ArrowLeft size={16} />{t('previous')}</button>{currentIndex < quiz.items.length - 1 ? <button type="button" className="primary-button" onClick={() => setCurrentIndex((index) => index + 1)}>{t('next')}<ArrowRight size={16} /></button> : <button type="button" className="primary-button" disabled={!allAnswered || busy} onClick={() => void submit()}>{busy ? t('loading') : t('submit')}<CheckCircle2 size={16} /></button>}</div>{!allAnswered && currentIndex === quiz.items.length - 1 && <p className="mt-3 text-xs text-amber-700">Answer all {quiz.items.length} questions before submitting.</p>}</section> : <QuizResultPanel result={result} updates={updates} beforeRecommendations={beforeRecommendations} afterRecommendations={afterRecommendations} onRestart={() => { setResult(null); setAnswers({}); setCurrentIndex(0) }} />}
  </div></AppShell>
}

function QuizResultPanel({ result, updates, beforeRecommendations, afterRecommendations, onRestart }: { result: QuizResult; updates: { competency: string; before: number; after: number; target: number }[]; beforeRecommendations: LearningResource[]; afterRecommendations: LearningResource[]; onRestart: () => void }) {
  const { language, t } = useLanguage()
  return <section className="mt-8 space-y-6"><div className="panel p-6 sm:p-8"><div className="flex flex-wrap items-end justify-between gap-5"><div><p className="eyebrow text-teal">{t('assessmentResult')}</p><h2 className="mt-2 text-4xl font-semibold tracking-tight text-navy">{result.score}%</h2><p className="mt-2 text-sm text-slate-500">{result.correct_answers} {t('correct')} of {result.total_questions} · competency evidence updated</p></div><div className="rounded-2xl bg-[#eef7f6] p-5 text-right"><p className="text-xs font-bold uppercase tracking-wide text-teal">Adaptive loop</p><p className="mt-2 text-sm font-semibold text-navy">New evidence is now reflected in your profile.</p></div></div></div><div className="panel p-6 sm:p-8"><div className="flex items-center gap-3"><span className="status-icon"><Target size={18} /></span><div><p className="eyebrow text-teal">Before and after</p><h2 className="mt-2 text-xl font-semibold text-navy">Competency evidence update</h2></div></div><div className="mt-6 space-y-5">{updates.map((item) => <div key={item.competency}><div className="flex flex-wrap items-center justify-between gap-2"><span className="font-semibold text-navy">{item.competency}</span><span className="text-xs font-bold text-teal">{item.before}% → {item.after}% · gap {Math.max(0, item.target - item.before).toFixed(1)} → {Math.max(0, item.target - item.after).toFixed(1)} pts</span></div><div className="mt-2"><ScoreBar value={item.after} target={item.target} /></div></div>)}</div><p className="mt-5 text-xs leading-5 text-slate-500">Scores are derived from the existing evidence aggregator; this screen does not accept or calculate a score locally.</p></div><div className="panel p-6 sm:p-8"><p className="eyebrow text-teal">Recommendation refresh</p><h2 className="mt-2 text-xl font-semibold text-navy">What should happen next?</h2><div className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-xl border border-line p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Before quiz</p><p className="mt-2 text-sm font-semibold text-navy">{beforeRecommendations[0]?.title || 'No recommendation recorded'}</p><p className="mt-1 text-xs text-slate-500">{beforeRecommendations[0]?.source || '—'}</p></div><div className="rounded-xl border border-teal/30 bg-[#eef7f6] p-4"><p className="text-xs font-bold uppercase tracking-wide text-teal">After quiz</p><p className="mt-2 text-sm font-semibold text-navy">{afterRecommendations[0]?.title || 'Recalculation complete'}</p><p className="mt-1 text-xs text-slate-500">{afterRecommendations[0]?.source || 'Open the learning path for the updated ranking.'}</p></div></div><Link className="primary-button mt-5" to="/employee/learning-path">{t('learningPath')} <ArrowRight size={16} /></Link></div><div className="panel p-6 sm:p-8"><div className="flex items-center gap-3"><span className="status-icon"><ClipboardCheck size={18} /></span><div><p className="eyebrow text-teal">{t('explanation')}</p><h2 className="mt-2 text-xl font-semibold text-navy">{t('explanation')}</h2></div></div><div className="mt-5 space-y-3">{result.explanations.map((item) => <details className="rounded-xl border border-line p-4" key={item.item_id}><summary className="flex cursor-pointer items-center gap-3 text-sm font-semibold text-navy"><span className={item.is_correct ? 'text-teal' : 'text-red-600'}>{item.is_correct ? <CheckCircle2 size={16} /> : <XCircle size={16} />}</span><span className="flex-1">{t('quiz')} {item.item_id}</span><span className="text-xs font-normal text-slate-500">{t('explanation')}</span></summary><div className="mt-3 border-t border-line pt-3 text-sm leading-6 text-slate-600"><p>{item.explanation}</p><p className="mt-2 text-xs text-slate-500">Correct option: {String.fromCharCode(65 + item.correct_index)} · Source chunk {String(item.source.chunk_id || '—')} {item.source.page_number ? `· Page ${String(item.source.page_number)}` : ''}</p></div></details>)}</div></div><button type="button" className="secondary-button" onClick={onRestart}><RotateCcw size={16} />{language === 'hi' ? 'फिर से प्रयास करें' : 'Try again'}</button></section>
}
