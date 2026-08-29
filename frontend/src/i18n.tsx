import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useAuth } from './auth/AuthContext'

export type LanguageCode = 'en' | 'hi'

export type TranslationKey =
  | 'dashboard' | 'myProfile' | 'myCompetencies' | 'fracIntelligence' | 'assessment' | 'skillGaps'
  | 'learningPath' | 'quiz' | 'statbot' | 'workspace' | 'comingNext' | 'plannedModules'
  | 'currentLevel' | 'requiredLevel' | 'skillGap' | 'recommendations' | 'progress'
  | 'startLearning' | 'continueLearning' | 'markComplete' | 'whyRecommendation'
  | 'assessmentResult' | 'submit' | 'correct' | 'incorrect' | 'explanation' | 'ask' | 'next'
  | 'previous' | 'answered' | 'loading' | 'language' | 'english' | 'hindi'
  | 'prototypeMultilingual' | 'notAvailable' | 'notStarted' | 'inProgress' | 'completed'

const translations: Record<LanguageCode, Record<TranslationKey, string>> = {
  en: {
    dashboard: 'Dashboard', myProfile: 'My profile', myCompetencies: 'My competencies', fracIntelligence: 'FRAC intelligence',
    assessment: 'Assessment', skillGaps: 'Skill gaps', learningPath: 'Learning path', quiz: 'Quiz', statbot: 'StatBot assistant',
    workspace: 'Workspace', comingNext: 'Coming next', plannedModules: 'Planned modules', currentLevel: 'Current level',
    requiredLevel: 'Required level', skillGap: 'Skill gap', recommendations: 'Recommendations', progress: 'Progress',
    startLearning: 'Start learning', continueLearning: 'Continue learning', markComplete: 'Mark complete',
    whyRecommendation: 'Why this recommendation?', assessmentResult: 'Assessment result', submit: 'Submit', correct: 'Correct',
    incorrect: 'Incorrect', explanation: 'Explanation', ask: 'Ask StatBot', next: 'Next', previous: 'Previous', answered: 'answered', loading: 'Loading…',
    language: 'Language', english: 'English', hindi: 'हिन्दी', prototypeMultilingual: 'Prototype multilingual content', notAvailable: 'Hindi content not available',
    notStarted: 'Not started', inProgress: 'In progress', completed: 'Completed',
  },
  hi: {
    dashboard: 'डैशबोर्ड', myProfile: 'मेरी प्रोफ़ाइल', myCompetencies: 'मेरी दक्षताएँ', fracIntelligence: 'FRAC जानकारी',
    assessment: 'आकलन', skillGaps: 'कौशल अंतर', learningPath: 'सीखने का मार्ग', quiz: 'क्विज़', statbot: 'StatBot सहायक',
    workspace: 'कार्यस्थान', comingNext: 'आगे आने वाला', plannedModules: 'नियोजित मॉड्यूल', currentLevel: 'वर्तमान स्तर',
    requiredLevel: 'आवश्यक स्तर', skillGap: 'कौशल अंतर', recommendations: 'सिफारिशें', progress: 'प्रगति',
    startLearning: 'सीखना शुरू करें', continueLearning: 'सीखना जारी रखें', markComplete: 'पूर्ण चिह्नित करें',
    whyRecommendation: 'यह सिफारिश क्यों?', assessmentResult: 'आकलन परिणाम', submit: 'जमा करें', correct: 'सही',
    incorrect: 'गलत', explanation: 'व्याख्या', ask: 'StatBot से पूछें', next: 'अगला', previous: 'पिछला', answered: 'उत्तर दिए गए', loading: 'लोड हो रहा है…',
    language: 'भाषा', english: 'English', hindi: 'हिन्दी', prototypeMultilingual: 'प्रोटोटाइप बहुभाषी सामग्री', notAvailable: 'हिन्दी सामग्री उपलब्ध नहीं है',
    notStarted: 'शुरू नहीं हुआ', inProgress: 'प्रगति में', completed: 'पूर्ण',
  },
}

interface LanguageContextValue {
  language: LanguageCode
  setLanguage: (language: LanguageCode) => void
  t: (key: TranslationKey) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [language, setLanguageState] = useState<LanguageCode>('en')

  useEffect(() => {
    const stored = user ? localStorage.getItem(`stat-growth-language:${user.id}`) : null
    setLanguageState(stored === 'hi' ? 'hi' : 'en')
  }, [user?.id])

  const setLanguage = (next: LanguageCode) => {
    setLanguageState(next)
    if (user) localStorage.setItem(`stat-growth-language:${user.id}`, next)
  }

  const value = useMemo(() => ({ language, setLanguage, t: (key: TranslationKey) => translations[language][key] }), [language, user?.id])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage must be used within LanguageProvider')
  return context
}
