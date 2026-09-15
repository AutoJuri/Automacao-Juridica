import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/custas-dare')({
  beforeLoad: requireAuth,
  component: function CustasDareRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Custas DARE"
        descricao="Guia de custas DARE. Em construção — nenhum boleto ou guia é gerado daqui por enquanto."
      />
    )
  },
})
