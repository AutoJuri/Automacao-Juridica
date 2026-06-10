import { createFileRoute, redirect } from '@tanstack/react-router'
import { LoginPage } from '#/features/auth/LoginPage'
import { useAuthStore } from '#/store/auth.store'

export const Route = createFileRoute('/login')({
  beforeLoad: () => {
    const { isAuthenticated } = useAuthStore.getState()
    if (isAuthenticated) {
      throw redirect({ to: '/' })
    }
  },
  component: LoginPage,
})
