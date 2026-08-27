import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

import { DashboardPage } from '#/features/processos/DashboardPage'
import { requireAuth } from '#/lib/route-guards'

const searchSchema = z.object({
  processo: z.string().uuid().optional().catch(undefined),
})

export const Route = createFileRoute('/')({
  beforeLoad: requireAuth,
  validateSearch: searchSchema,
  component: function IndexRoute() {
    const { processo } = Route.useSearch()
    return <DashboardPage processoInicial={processo} />
  },
})
