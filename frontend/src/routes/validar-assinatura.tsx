import { createFileRoute } from '@tanstack/react-router'

import { SecaoPlaceholderPage } from '#/features/secoes/SecaoPlaceholderPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/validar-assinatura')({
  beforeLoad: requireAuth,
  component: function ValidarAssinaturaRoute() {
    return (
      <SecaoPlaceholderPage
        titulo="Validar Assinatura"
        descricao="Validação de assinatura digital de documentos. Em construção — nenhum arquivo é enviado ou verificado daqui por enquanto."
      />
    )
  },
})
