import { createFileRoute } from '@tanstack/react-router'
import { DashboardPage } from '#/features/processos/DashboardPage'

export const Route = createFileRoute('/')({
  component: DashboardPage,
})
