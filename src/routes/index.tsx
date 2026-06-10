import { createFileRoute, redirect } from '@tanstack/react-router'
import { DashboardPage } from '#/features/processos/DashboardPage'
import { useAuthStore } from '#/store/auth.store'

export const Route = createFileRoute('/')({
  beforeLoad: () => {
    const { isAuthenticated } = useAuthStore.getState()
    if (!isAuthenticated) {
      throw redirect({ to: '/login' })
    }
  },
  component: DashboardPage,
})
