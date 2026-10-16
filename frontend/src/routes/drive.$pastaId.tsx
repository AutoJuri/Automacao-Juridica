import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/drive/$pastaId')({
  beforeLoad: requireAuth,
  pendingComponent: function PastaPendente() {
    return (
      <SecaoShell>
        <EstadoCarregando mensagem="Carregando pasta…" />
      </SecaoShell>
    )
  },
})
