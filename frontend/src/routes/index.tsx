import { createFileRoute } from '@tanstack/react-router'
import { DashboardPage } from '#/features/processos/DashboardPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/')({
  beforeLoad: requireAuth,
  component: DashboardPage,
})
