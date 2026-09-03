import { createFileRoute } from '@tanstack/react-router'

import { ConsultaPastaPage } from '#/features/consulta/ConsultaPastaPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/consulta-pasta')({
  beforeLoad: requireAuth,
  component: ConsultaPastaPage,
})
