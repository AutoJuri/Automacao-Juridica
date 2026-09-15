import { createFileRoute } from '@tanstack/react-router'
import { ElaboracaoPage } from '#/features/elaboracao/ElaboracaoPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/elaboracao/$processoId')({
  beforeLoad: requireAuth,
  component: function ElaboracaoRoute() {
    const { processoId } = Route.useParams()
    return <ElaboracaoPage processoId={processoId} />
  },
})
