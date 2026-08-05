import { createFileRoute, redirect } from '@tanstack/react-router'
import { ElaboracaoPage } from '#/features/elaboracao/ElaboracaoPage'
import { useAuthStore } from '#/store/auth.store'
import { processosMockados } from '#/features/processos/processos.mock'

export const Route = createFileRoute('/elaboracao/$processoId')({
  beforeLoad: ({ params }) => {
    const { isAuthenticated } = useAuthStore.getState()
    if (!isAuthenticated) {
      throw redirect({ to: '/login' })
    }

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
