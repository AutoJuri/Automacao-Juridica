import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/organizacoes/$orgId')({
  beforeLoad: requireAuth,
  pendingComponent: function OrganizacaoPendente() {
    return (
      <SecaoShell scroll={false}>
        <EstadoCarregando mensagem="Carregando a organização…" />
      </SecaoShell>
    )
  },
})
