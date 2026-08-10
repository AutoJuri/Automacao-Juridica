import { createFileRoute, redirect } from '@tanstack/react-router'
import { ElaboracaoPage } from '#/features/elaboracao/ElaboracaoPage'
import { processosMockados } from '#/features/processos/processos.mock'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/elaboracao/$processoId')({
  beforeLoad: ({ params }) => {
    requireAuth()

    const id = Number(params.processoId)
    const existe = processosMockados.some((p) => p.id === id)
    if (!existe) {
      throw redirect({ to: '/' })
    }
  },
  component: function ElaboracaoRoute() {
    const { processoId } = Route.useParams()
    return <ElaboracaoPage processoId={Number(processoId)} />
  },
})
