/**
 * Contratos de resposta das rotas de autenticação, espelhando os schemas
 * Pydantic do backend (backend/app/schemas/auth.py).
 *
 * Ficam separados de auth.api.ts porque lib/axios.ts também precisa deles e
 * não deve depender do módulo de feature em tempo de execução.
 */

import type { AuthUser } from '#/store/auth.store'

export interface TokenResponse {
  access_token: string
  token_type: string
  /** Validade do access token em segundos. */
  expires_in: number
  user: AuthUser
}

export interface MessageResponse {
  message: string
}
