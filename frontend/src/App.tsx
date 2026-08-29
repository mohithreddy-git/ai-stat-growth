import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { EmployeeAssessmentPage } from './pages/EmployeeAssessmentPage'
import { EmployeeCompetenciesPage } from './pages/EmployeeCompetenciesPage'
import { EmployeeLearningPathPage } from './pages/EmployeeLearningPathPage'
import { EmployeeIntelligencePage } from './pages/EmployeeIntelligencePage'
import { EmployeeAssistantPage } from './pages/EmployeeAssistantPage'
import { EmployeeProfilePage } from './pages/EmployeeProfilePage'
import { EmployeeSkillGapsPage } from './pages/EmployeeSkillGapsPage'
import { EmployeeQuizPage } from './pages/EmployeeQuizPage'
import { AdminIntelligencePage } from './pages/AdminIntelligencePage'
import { WorkspaceHomePage } from './pages/WorkspaceHomePage'
import { TrainerAssessmentStudioPage } from './pages/TrainerAssessmentStudioPage'

function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? `/${user.role.toLowerCase()}/dashboard` : '/login'} replace />
}

export default function App() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<ProtectedRoute roles={['EMPLOYEE']} />}>
        <Route path="/employee/dashboard" element={<WorkspaceHomePage />} />
        <Route path="/employee/profile" element={<EmployeeProfilePage />} />
        <Route path="/employee/competencies" element={<EmployeeCompetenciesPage />} />
        <Route path="/employee/intelligence" element={<EmployeeIntelligencePage />} />
        <Route path="/employee/assessment" element={<EmployeeAssessmentPage />} />
        <Route path="/employee/skill-gaps" element={<EmployeeSkillGapsPage />} />
        <Route path="/employee/learning-path" element={<EmployeeLearningPathPage />} />
        <Route path="/employee/quiz" element={<EmployeeQuizPage />} />
        <Route path="/employee/assistant" element={<EmployeeAssistantPage />} />
      </Route>
      <Route element={<ProtectedRoute roles={['ADMIN']} />}><Route path="/admin/dashboard" element={<AdminIntelligencePage />} /></Route>
      <Route element={<ProtectedRoute roles={['TRAINER']} />}>
        <Route path="/trainer/dashboard" element={<WorkspaceHomePage />} />
        <Route path="/trainer/assessment-studio" element={<TrainerAssessmentStudioPage />} />
      </Route>
    </Route>
    <Route path="*" element={<HomeRedirect />} />
  </Routes>
}
