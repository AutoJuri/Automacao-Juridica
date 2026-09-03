import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/drive')({
  beforeLoad: requireAuth,
  component: function DriveRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Drive"
        descricao="Arquivos e documentos do escritório. Ainda não tem conteúdo — a página existe só para a nova navegação."
      />
    )
  },
})
