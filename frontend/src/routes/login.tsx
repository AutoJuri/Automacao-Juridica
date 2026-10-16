import { createFileRoute, redirect } from '@tanstack/react-router'
import { z } from 'zod'

import { LoginPage } from '#/features/auth/LoginPage'
import { destinoConvite, tokenDoDestino } from '#/features/organizations/organizations.redirect'
import { useAuthStore } from '#/store/auth.store'

const searchSchema = z.object({
  redirect: z.string().optional().catch(undefined),
  email: z.string().max(255).optional().catch(undefined),
  mode: z.enum(['login', 'register']).optional().catch(undefined),
})

export const Route = createFileRoute('/login')({
  validateSearch: searchSchema,
  beforeLoad: ({ search }) => {
    if (!useAuthStore.getState().isAuthenticated) {
      return
    }
    const destino = destinoConvite(search.redirect)
    if (destino) {
      throw redirect({
        to: '/convite/$token',
        params: { token: tokenDoDestino(destino) },
      })
    }
    throw redirect({ to: '/' })
  },
  component: function LoginRoute() {
    const { redirect: redirectTo, email, mode } = Route.useSearch()
    const destino = destinoConvite(redirectTo)
    return (
      <LoginPage
        redirectTo={destino}
        emailConvite={destino && mode === 'register' ? email : undefined}
        modoInicial={mode === 'register' ? 'register' : 'login'}
      />
    )
  },
})
