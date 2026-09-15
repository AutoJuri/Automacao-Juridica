import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/tarefas')({
  beforeLoad: requireAuth,
  component: function TarefasRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Tarefas"
        descricao="Tarefas e prazos do escritório. Ainda não tem conteúdo — a página existe só para a nova navegação."
      />
    )
  },
})
