export type Role = 'EMPLOYEE' | 'ADMIN' | 'TRAINER'
export type ResourceType = 'course' | 'training_programme'
export type ProgressStatus = 'not_started' | 'in_progress' | 'completed'
export type GapSeverity = 'critical' | 'high' | 'medium' | 'low'

export interface UserSummary {
  id: number
  employee_id: string
  email: string
  full_name: string
  designation: string
  division: string
  current_assignment: string
  years_experience: number
  domain: string
  current_role: string
  career_goal: string
  role: Role
  department: string
  is_demo: boolean
}

export interface EmployeeProfile extends UserSummary {
  educational_qualification: string
  previous_trainings: string[]
}

export interface BootstrapData {
  app_name: string
  environment: string
  phase: string
  ai_provider: string
  demo_mode: boolean
  seeded_counts: Record<string, number>
  planned_modules: string[]
}

export interface DemoResetResponse {
  status: string
  message: string
  seeded_counts: Record<string, number>
  runtime_counts: Record<string, number>
}

export interface TelemetryEvent {
  eid: string
  ets: number
  ver: string
  mid: string
  actor: Record<string, unknown>
  context: Record<string, unknown>
  object: Record<string, unknown>
  edata: Record<string, unknown>
  tags: string[]
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserSummary
}

export interface CompetencyFrameworkItem {
  id: number
  code: string
  name: string
  category: string
  description: string
  beginner_definition: string
  intermediate_definition: string
  advanced_definition: string
  required_level: number
  required_score: number
  weight: number
}

export interface EmployeeCompetency {
  competency_id: number
  code: string
  name: string
  category: string
  current_score: number
  current_level: number
  current_level_label: string
  target_level: number
  target_level_label: string
  required_score: number
  delta_from_previous: number | null
  last_assessed_at: string | null
  confidence: number
  evidence_count: number
  description: string
}

export interface CompetencyProfile {
  user_id: number
  overall_readiness: number
  category_scores: Record<string, number>
  competencies: EmployeeCompetency[]
  strengths: EmployeeCompetency[]
  weaknesses: EmployeeCompetency[]
}

export interface CompetencyDomainSummaryItem {
  name: string
  count: number
  average_current_score: number | null
  average_target_score: number | null
}

export interface CompetencyDomainSummary {
  domains: CompetencyDomainSummaryItem[]
  total_competencies: number
}

export interface SkillGap {
  competency_id: number
  competency: string
  code: string
  category: string
  current_score: number
  required_score: number
  gap: number
  severity: GapSeverity
  priority_score: number
  role_relevance: number
  department_priority: number
  future_demand: number
  explanation: string
  recommended_next_action: string
  current_level: string
  required_level: string
}

export interface LearningResource {
  id: number
  resource_type: ResourceType
  external_id: string
  title: string
  source: string
  competency_id: number
  competency: string
  description: string
  duration: number
  duration_label: string
  requested_language: 'en' | 'hi'
  localized: boolean
  localization_label: string | null
  title_en: string | null
  title_hi: string | null
  description_en: string | null
  description_hi: string | null
  reason_en: string | null
  reason_hi: string | null
  expected_outcome_en: string | null
  expected_outcome_hi: string | null
  difficulty: string
  relevance_score: number
  priority: GapSeverity
  reason: string
  expected_outcome: string
  current_score: number
  required_score: number
  gap: number
  role_relevance: number
  department_priority: number
  future_demand: number
  expected_improvement: number
  url: string
  is_prototype: boolean
  activities: string[]
  explanation_data: Record<string, unknown>
  historical_effectiveness: number
  progress_status: ProgressStatus
  completion_percent: number
}

export interface LearningProgress {
  id: number
  resource_type: ResourceType
  resource_id: number
  resource_title: string
  source: string
  status: ProgressStatus
  completion_percent: number
  learning_hours: number
  last_activity_at: string | null
}

export interface AssessmentSummary {
  id: number
  title: string
  description: string
  category: string
  question_count: number
  competency_count: number
}

export interface AssessmentQuestion {
  id: number
  competency_id: number
  competency: string
  category: string
  question: string
  options: string[]
  difficulty: string
  explanation: string | null
  requested_language: 'en' | 'hi'
  localized: boolean
}

export interface AssessmentDetail extends AssessmentSummary {
  questions: AssessmentQuestion[]
}

export interface AssessmentStart {
  attempt_id: number
  assessment: AssessmentDetail
  started_at: string
}

export interface AssessmentAnswerReview {
  question_id: number
  competency: string
  selected_answer: string
  correct_answer: string
  is_correct: boolean
  explanation: string
}

export interface CompetencyResult {
  competency_id: number
  competency: string
  category: string
  previous_score: number
  assessment_score: number
  updated_score: number
  delta: number
  required_score: number
  gap_after: number
}

export interface AssessmentResult {
  attempt_id: number
  assessment_id: number
  assessment_title: string
  status: 'completed'
  overall_score: number
  percentage: number
  correct_answers: number
  incorrect_answers: number
  total_questions: number
  category_scores: Record<string, number>
  strengths: string[]
  weaknesses: string[]
  competency_results: CompetencyResult[]
  answer_review: AssessmentAnswerReview[]
  completed_at: string
}

export interface Course {
  id: number
  course_id: string
  title: string
  description: string
  source: string
  duration_hours: number
  difficulty: string
  language: string
  requested_language: 'en' | 'hi'
  localized: boolean
  localization_label: string | null
  title_en: string
  title_hi: string | null
  description_en: string
  description_hi: string | null
  skills: string[]
  competency_ids: number[]
  role_tags: string[]
  department_tags: string[]
  url: string
  completion_status: ProgressStatus
  is_prototype: boolean
}

export interface TrainingProgramme {
  id: number
  programme_id: string
  programme_name: string
  description: string
  category: string
  duration_days: number
  target_group: string
  requested_language: 'en' | 'hi'
  localized: boolean
  localization_label: string | null
  title_en: string
  title_hi: string | null
  description_en: string
  description_hi: string | null
  competency_ids: number[]
  role_tags: string[]
  recommended_for: string[]
  schedule: string
  url: string
  source: string
  is_prototype: boolean
}

export interface EmployeeDashboard {
  profile: EmployeeProfile
  competency: CompetencyProfile
  skill_gaps: SkillGap[]
  recommendations: LearningResource[]
  learning_progress: LearningProgress[]
  learning_hours: number
  completed_courses: number
  assessment_score: number | null
  recent_assessment_id: number | null
}

export interface FRACActivityRequirement {
  activity_id: number
  competency_id: number
  activity: string
  criticality: number
  required_level: number
  required_score: number
  importance: number
  current_score: number
  current_level: number
  current_level_label: string
  gap: number
}

export interface FRACProfile {
  employee_id: number
  position_id: number | null
  position: string | null
  role_id: number | null
  role: string | null
  activities: FRACActivityRequirement[]
  competencies: { competency_id: number; competency: string; type: string; required_for: string[] }[]
}

export interface CompetencyVector {
  employee_id: number
  dimensions: { competency_id: number; code: string; competency: string; weight: number; current_score: number; target_score: number }[]
  current_vector: number[]
  target_vector: number[]
  competency_specific_gaps: { competency_id: number; competency: string; gap: number; current: number; target: number }[]
  critical_gaps: { competency_id: number; competency: string; gap: number; current: number; target: number }[]
  weighted_distance: number
  cosine_similarity: number
  overall_alignment_score: number
}

export interface EvidenceRecord {
  id: number
  competency_id: number
  source_type: string
  source_id: string | null
  score: number
  confidence: number
  metadata: Record<string, unknown>
  created_at: string
}

export interface VelocityMetrics {
  employee_id: number
  window_days: number
  learning_velocity: number
  learning_hours: number
  completed_resources: number
  assessment_accuracy: number
  completion_velocity: number
  engagement_rate: number
  recommendation_acceptance_rate: number
  competency_improvement_rate: number
}

export interface DocumentRecord {
  id: number
  filename: string
  content_type: string
  size_bytes: number
  status: string
  chunk_count: number
  processing_error: string | null
  created_at: string
}

export interface AssessmentItem {
  id: number
  document_id: number | null
  question: string
  options: string[]
  correct_index: number
  explanation: string
  competency_id: number
  topic: string
  difficulty: string
  source: Record<string, unknown>
  status: string
  confidence: number
  generated_by: string
  created_at: string
}

export interface PublishedQuiz {
  id: number
  title: string
  document_id: number | null
  item_ids: number[]
  status: string
  created_at: string
}

export interface PublishedQuizItem {
  id: number
  question: string
  options: string[]
  competency_id: number
  topic: string
  difficulty: string
  source: Record<string, unknown>
  localized?: boolean
}

export interface PublishedQuizDetails extends PublishedQuiz {
  requested_language?: 'en' | 'hi'
  items: PublishedQuizItem[]
}

export interface QuizResult {
  attempt_id: number
  quiz_id: number
  score: number
  requested_language?: 'en' | 'hi'
  correct_answers: number
  total_questions: number
  topic_performance: Record<string, number>
  explanations: { item_id: number; is_correct: boolean; correct_index: number; explanation: string; source: Record<string, unknown> }[]
}

export interface AdminOverview {
  total_officials: number
  average_competency: number
  critical_skill_gaps: number
  training_completion_rate: number
  assessment_performance: number
  learning_hours: number
  department_count: number
}

export interface AdminDepartment {
  department_id: number
  department: string
  officials: number
  average_competency: number
  critical_gaps: number
  average_gap: number
}

export interface FutureDemand {
  competency_id: number
  competency: string
  current_demand: number
  projected_demand: number
  growth_rate: number
  priority: string
  period: string
  source: string
  confidence: number
  affected_departments: string[]
}
