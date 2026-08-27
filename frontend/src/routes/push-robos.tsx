import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/push-robos')({
  beforeLoad: requireAuth,
  component: function PushRobosRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Push Robôs"
        descricao="Configuração de alertas automáticos. Em construção. As notificações in-app atuais continuam no sino à direita da barra."
      />
    )
  },
})
