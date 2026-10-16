import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/convites')({
  beforeLoad: requireAuth,
  pendingComponent: function ConvitesPendentes() {
    return (
      <SecaoShell scroll={false}>
        <EstadoCarregando mensagem="Carregando os convites…" />
      </SecaoShell>
    )
  },
})
