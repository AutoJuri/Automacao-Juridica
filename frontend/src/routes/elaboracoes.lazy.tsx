import { createLazyFileRoute } from '@tanstack/react-router'

import { ElaboracoesPage } from '#/features/elaboracao/ElaboracoesPage'

export const Route = createLazyFileRoute('/elaboracoes')({
  component: ElaboracoesPage,
})
