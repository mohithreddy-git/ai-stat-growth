import type {
  AssessmentResult,
  AssessmentStart,
  AssessmentSummary,
  AuthResponse,
  BootstrapData,
  CompetencyDomainSummary,
  CompetencyFrameworkItem,
  DemoResetResponse,
  CompetencyProfile,
  Course,
  EmployeeDashboard,
  EmployeeProfile,
  LearningProgress,
  LearningResource,
  PublishedQuizDetails,
  QuizResult,
  SkillGap,
  TrainingProgramme,
  TelemetryEvent,
  UserSummary,
} from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').replace(/\/$/, '')

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('stat-growth-token')
  const headers = new Headers(options.headers)
  if (typeof options.body === 'string' && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw new Error('Cannot reach the AI STAT-GROWTH API. Check that the backend is running.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail || `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  login: (email: string, password: string) => request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }),
  me: () => request<UserSummary>('/users/me'),
  bootstrap: () => request<BootstrapData>('/bootstrap'),
  demoReset: () => request<DemoResetResponse>('/demo/reset', { method: 'POST' }),
  profile: (userId: number) => request<EmployeeProfile>(`/users/${userId}`),
  dashboard: (userId: number, language: 'en' | 'hi' = 'en') => request<EmployeeDashboard>(`/users/${userId}/dashboard?language=${language}`),
  competencies: (userId: number) => request<CompetencyProfile>(`/users/${userId}/competencies`),
  competencyDomainSummary: (userId: number) => request<CompetencyDomainSummary>(`/users/${userId}/competency-domain-summary`),
  framework: () => request<CompetencyFrameworkItem[]>('/competencies'),
  skillGaps: (userId: number) => request<SkillGap[]>(`/users/${userId}/skill-gaps`),
  recommendations: (userId: number, language: 'en' | 'hi' = 'en') => request<LearningResource[]>(`/users/${userId}/recommendations?language=${language}`),
  learningProgress: (userId: number) => request<LearningProgress[]>(`/users/${userId}/learning-progress`),
  saveLearningProgress: (userId: number, payload: {
    resource_type: 'course' | 'training_programme'
    resource_id: number
    status: 'not_started' | 'in_progress' | 'completed'
    completion_percent: number
    learning_hours: number
  }) => request<LearningProgress>(`/users/${userId}/learning-progress`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  assessments: () => request<AssessmentSummary[]>('/assessments'),
  startAssessment: (assessmentId: number, language: 'en' | 'hi' = 'en') => request<AssessmentStart>('/assessments/start', {
    method: 'POST',
    body: JSON.stringify({ assessment_id: assessmentId, language }),
  }),
  submitAssessment: (attemptId: number, answers: { question_id: number; answer: string }[]) => request<AssessmentResult>(`/assessments/${attemptId}/submit`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  }),
  assessmentResult: (attemptId: number) => request<AssessmentResult>(`/assessments/${attemptId}/result`),
  courses: (language: 'en' | 'hi' = 'en') => request<Course[]>(`/courses?language=${language}`),
  trainingProgrammes: (language: 'en' | 'hi' = 'en') => request<TrainingProgramme[]>(`/training-programmes?language=${language}`),
  fracProfile: (userId: number) => request<import('../types').FRACProfile>(`/users/${userId}/frac-profile`),
  competencyVector: (userId: number) => request<import('../types').CompetencyVector>(`/users/${userId}/competency-vector`),
  evidence: (userId: number) => request<import('../types').EvidenceRecord[]>(`/users/${userId}/evidence`),
  telemetry: (payload: Record<string, unknown>) => request<{ mid: string; accepted: boolean; duplicate: boolean }>('/telemetry/events', { method: 'POST', body: JSON.stringify(payload) }),
  velocity: (userId: number) => request<import('../types').VelocityMetrics>(`/telemetry/learner/${userId}/velocity`),
  uploadDocument: (file: File) => { const form = new FormData(); form.append('upload', file); return request<import('../types').DocumentRecord>('/documents/upload', { method: 'POST', body: form }) },
  documents: () => request<import('../types').DocumentRecord[]>('/documents'),
  processDocument: (documentId: number) => request<import('../types').DocumentRecord>(`/documents/${documentId}/process`, { method: 'POST' }),
  generateItems: (payload: { document_id: number; count: number; topic: string; difficulty: 'easy' | 'medium' | 'hard' | 'mixed'; competency_id?: number }) => request<import('../types').AssessmentItem[]>('/assessment-items/generate', { method: 'POST', body: JSON.stringify(payload) }),
  reviewQueue: () => request<import('../types').AssessmentItem[]>('/assessment-items/review-queue'),
  approveItem: (itemId: number) => request<import('../types').AssessmentItem>(`/assessment-items/${itemId}/approve`, { method: 'POST', body: JSON.stringify({}) }),
  publishQuiz: (title: string, itemIds: number[]) => request<import('../types').PublishedQuiz>('/quizzes/publish', { method: 'POST', body: JSON.stringify({ title, item_ids: itemIds }) }),
  getQuiz: (quizId: number, language: 'en' | 'hi' = 'en') => request<PublishedQuizDetails>(`/quizzes/${quizId}?language=${language}`),
  submitQuiz: (quizId: number, answers: Record<number, number>, language: 'en' | 'hi' = 'en') => request<QuizResult>(`/quizzes/${quizId}/submit`, { method: 'POST', body: JSON.stringify({ answers, language }) }),
  adminOverview: () => request<import('../types').AdminOverview>('/admin/overview'),
  adminDepartments: () => request<import('../types').AdminDepartment[]>('/admin/departments'),
  adminGaps: () => request<Record<string, unknown>[]>('/admin/skill-gaps'),
  adminTraining: () => request<Record<string, unknown>[]>('/admin/training-effectiveness'),
  adminForecast: () => request<import('../types').FutureDemand[]>('/admin/forecast'),
  telemetrySummary: () => request<Record<string, number>>('/telemetry/organization/summary'),
  recentTelemetryEvents: () => request<TelemetryEvent[]>('/telemetry/organization/recent'),
  assistant: (payload: { message: string; mode: 'general' | 'document'; document_id?: number; language?: 'en' | 'hi' }) => request<{ answer: string; mode: 'general' | 'document'; sources: Record<string, unknown>[]; provider: string; requested_language?: 'en' | 'hi'; localized?: boolean }>('/ai/chat', { method: 'POST', body: JSON.stringify(payload) }),
}
