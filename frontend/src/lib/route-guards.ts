/**
 * Guardas usadas no `beforeLoad` das rotas.
 *
 * Nota: isso é apenas visual/navegação. O backend é a fonte de verdade — toda
 * rota da API valida o access token e responde 401/403 por conta própria.
 */

import { redirect } from '@tanstack/react-router'

import { useAuthStore } from '#/store/auth.store'

/** Rotas do painel: manda visitante para o login. */
export function requireAuth(): void {
  if (!useAuthStore.getState().isAuthenticated) {
    throw redirect({ to: '/login' })
  }
}

/** Rotas públicas de auth: tira de lá quem já está logado. */
export function requireGuest(): void {
  if (useAuthStore.getState().isAuthenticated) {
    throw redirect({ to: '/' })
  }
}
