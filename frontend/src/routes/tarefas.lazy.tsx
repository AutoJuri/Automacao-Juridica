import { createLazyFileRoute } from '@tanstack/react-router'

import { TarefasPage } from '#/features/tarefas/TarefasPage'

export const Route = createLazyFileRoute('/tarefas')({
  component: TarefasPage,
})
