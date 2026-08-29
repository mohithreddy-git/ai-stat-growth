import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import type { Role } from '../types'

export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { user, isLoading, hasRole } = useAuth()
  const location = useLocation()

  if (isLoading) return <div className="min-h-screen grid place-items-center bg-mist text-slate-600">Restoring secure session…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !hasRole(...roles)) return <Navigate to={`/${user.role.toLowerCase()}/dashboard`} replace />
  return <Outlet />
}
