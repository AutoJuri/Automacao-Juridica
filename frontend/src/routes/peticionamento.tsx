import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/peticionamento')({
  beforeLoad: requireAuth,
  component: function PeticionamentoRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Peticionamento"
        descricao="Espaço para protocolar petições nos portais. Ainda não está em operação — por enquanto só o acompanhamento de autos em Autos & Gabinete está ativo."
      />
    )
  },
})
