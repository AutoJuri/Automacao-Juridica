import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/tarefas')({
  beforeLoad: requireAuth,
  pendingComponent: function TarefasPendentes() {
    return (
      <SecaoShell scroll={false}>
        <EstadoCarregando mensagem="Carregando o quadro…" />
      </SecaoShell>
    )
  },
})
