import { create } from 'zustand'

/** Dados públicos do usuário autenticado — nunca incluir password_hash ou campos internos. */
export interface AuthUser {
  id: string
  name: string
  email: string
}

interface AuthState {
  /**
   * Access token JWT de vida curta (15 min).
   * Armazenado APENAS em memória (Zustand). Jamais em localStorage ou sessionStorage —
   * ambos são vulneráveis a XSS.
   */
  accessToken: string | null
  user: AuthUser | null
  isAuthenticated: boolean

  /** Persiste token e dados do usuário no estado em memória após login bem-sucedido. */
  setAuth: (accessToken: string, user: AuthUser) => void

  /** Limpa todo o estado de autenticação. Chamado no logout e no interceptor 401. */
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,

  setAuth: (accessToken, user) => {
    set({ accessToken, user, isAuthenticated: true })
  },

  clearAuth: () => {
    set({ accessToken: null, user: null, isAuthenticated: false })
  },
}))
