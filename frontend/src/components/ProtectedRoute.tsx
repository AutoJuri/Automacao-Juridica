import { Navigate, Outlet } from '@tanstack/react-router'

import { useAuthStore } from '#/store/auth.store'

/**
 * Nota: Isso é apenas visual. A API deve retornar 401/403 para qualquer
 * requisição não autorizada — o backend é a fonte de verdade de autenticação.
 */
export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
