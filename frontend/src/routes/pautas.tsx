import { createFileRoute } from '@tanstack/react-router'

import { PautasPage } from '#/features/pautas/PautasPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/pautas')({
  beforeLoad: requireAuth,
  component: PautasPage,
})
