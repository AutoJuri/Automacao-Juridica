import { createFileRoute } from '@tanstack/react-router'

import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'

export const Route = createFileRoute('/convite/$token')({
  pendingComponent: function ConvitePendente() {
    return <EstadoCarregando mensagem="Carregando o convite…" />
  },
})
