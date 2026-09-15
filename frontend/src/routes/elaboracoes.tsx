import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/elaboracoes')({
  beforeLoad: requireAuth,
  component: function ElaboracoesRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Elaborações"
        descricao="Lista de minutas e peças em elaboração. Ainda não tem conteúdo. Para editar a minuta de um processo, use Elaborar no detalhe dos Andamentos."
      />
    )
  },
})
