import { createFileRoute } from '@tanstack/react-router'

import { ElaboracaoPage } from '#/features/elaboracao/ElaboracaoPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/elaboracao/$elaboracaoId')({
  beforeLoad: requireAuth,
  component: function ElaboracaoRoute() {
    const { elaboracaoId } = Route.useParams()
    return <ElaboracaoPage elaboracaoId={elaboracaoId} />
  },
})
