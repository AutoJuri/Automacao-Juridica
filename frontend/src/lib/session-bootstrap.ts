/**
 * Restauração de sessão no carregamento da aplicação.
 *
 * O access token vive apenas em memória (proteção contra XSS), então um F5
 * o descarta. O cookie HttpOnly de refresh, porém, sobrevive — uma tentativa
 * silenciosa de renovação no boot é o que mantém o usuário logado entre
 * recarregamentos de página.
 */

import { refreshAccessToken } from './axios'

let restauracao: Promise<void> | null = null

/**
 * Tenta restaurar a sessão uma única vez por carregamento da SPA.
 *
 * Falha é esperada e silenciosa: significa apenas que não há cookie válido,
 * ou seja, visitante não autenticado.
 */
export function ensureSessionRestored(): Promise<void> {
  if (!restauracao) {
    restauracao = refreshAccessToken().then(() => undefined)
  }

  return restauracao
}
