import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

import { SettingsPage } from '#/features/settings/SettingsPage'
import { requireAuth } from '#/lib/route-guards'

// `email` só existe no retorno do callback OAuth2 (redirect do backend) —
// ver backend/app/api/credentials.py::callback_email.
const searchSchema = z.object({
  email: z.enum(['conectado', 'erro']).optional().catch(undefined),
})

export const Route = createFileRoute('/configuracoes')({
  beforeLoad: requireAuth,
  validateSearch: searchSchema,
  component: function ConfiguracoesRoute() {
    const { email } = Route.useSearch()
    return <SettingsPage emailFeedback={email} />
  },
})
