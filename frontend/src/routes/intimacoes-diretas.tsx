import { createFileRoute } from '@tanstack/react-router'

import { IntimacoesDiretasPage } from '#/features/intimacoes/IntimacoesDiretasPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/intimacoes-diretas')({
  beforeLoad: requireAuth,
  component: IntimacoesDiretasPage,
})
