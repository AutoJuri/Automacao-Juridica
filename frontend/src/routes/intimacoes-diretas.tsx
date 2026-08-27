import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/intimacoes-diretas')({
  beforeLoad: requireAuth,
  component: function IntimacoesDiretasRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Intimações Diretas"
        descricao="Central de intimações diretas. Em construção. As intimações já coletadas continuam na ficha de cada processo em Autos & Gabinete, e o sino à direita lista as notificações in-app."
      />
    )
  },
})
