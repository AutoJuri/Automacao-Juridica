import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

import { AuthShell } from '#/features/auth/AuthShell'
import { ResetPasswordForm } from '#/features/auth/ResetPasswordForm'

// Rota pública: quem chega aqui vem do link de recuperação e, por definição,
// não consegue entrar na conta. O token no search param é a credencial da vez —
// a validação real dele acontece no backend.
const searchSchema = z.object({
  token: z.string().catch(''),
})

export const Route = createFileRoute('/redefinir-senha')({
  validateSearch: searchSchema,
  component: function RedefinirSenhaRoute() {
    const { token } = Route.useSearch()

    return (
      <AuthShell>
        <ResetPasswordForm token={token} />
      </AuthShell>
    )
  },
})
