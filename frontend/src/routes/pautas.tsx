import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/pautas')({
  beforeLoad: requireAuth,
  component: function PautasRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Pautas"
        descricao="Consulta de pautas de julgamento e audiência. Em construção. As audiências já coletadas pelo ciclo aparecem na ficha do processo em Autos & Gabinete."
      />
    )
  },
})
