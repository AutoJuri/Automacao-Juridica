import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/drive/')({
  beforeLoad: requireAuth,
  pendingComponent: function DrivePendente() {
    return (
      <SecaoShell>
        <EstadoCarregando mensagem="Carregando o Drive…" />
      </SecaoShell>
    )
  },
})
