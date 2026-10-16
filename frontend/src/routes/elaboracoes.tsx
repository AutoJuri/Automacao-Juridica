import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/elaboracoes')({
  beforeLoad: requireAuth,
  pendingComponent: function ElaboracoesPendentes() {
    return (
      <SecaoShell>
        <EstadoCarregando mensagem="Carregando elaborações…" />
      </SecaoShell>
    )
  },
})
