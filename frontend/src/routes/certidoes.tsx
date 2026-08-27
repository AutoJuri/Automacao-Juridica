import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/certidoes')({
  beforeLoad: requireAuth,
  component: function CertidoesRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Certidões"
        descricao="Emissão e consulta de certidões. Em construção — esta página ainda não consulta nenhum portal."
      />
    )
  },
})
