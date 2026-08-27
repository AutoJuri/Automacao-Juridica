import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/consulta-pasta')({
  beforeLoad: requireAuth,
  component: function ConsultaPastaRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Consulta / Pasta Digital"
        descricao="Consulta processual e pasta digital. Em construção. Nenhum documento é baixado ou armazenado daqui; os links da ficha do processo continuam abrindo o e-SAJ no próprio navegador."
      />
    )
  },
})
