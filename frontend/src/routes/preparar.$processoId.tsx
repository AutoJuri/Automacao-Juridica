import { createFileRoute } from '@tanstack/react-router'

import { PrepararPecaPage } from '#/features/elaboracao/PrepararPecaPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/preparar/$processoId')({
  beforeLoad: requireAuth,
  component: function PrepararRoute() {
    const { processoId } = Route.useParams()
    return <PrepararPecaPage processoId={processoId} />
  },
})
