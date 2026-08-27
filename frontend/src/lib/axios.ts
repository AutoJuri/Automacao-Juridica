import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

import type { TokenResponse } from '#/features/auth/auth.types'
import { queryClient } from '#/lib/query-client'
import { limparQueriesDaSessao } from '#/lib/session-queries'
import { useAuthStore } from '#/store/auth.store'

/** Marca uma request que já passou pelo fluxo de refresh, evitando loop infinito. */
type RequestConfigComRetry = InternalAxiosRequestConfig & { jaTentouRefresh?: boolean }

/**
 * Rotas onde um 401 é resposta legítima (credencial errada, cookie ausente ou
 * expirado) e não deve disparar tentativa de refresh.
 */
const ROTAS_SEM_REFRESH = ['/auth/login', '/auth/cadastro', '/auth/refresh']

/**
 * Instância base do Axios.
 * A baseURL é lida de VITE_API_URL — única variável VITE_* permitida neste projeto.
 * Nunca adicione chaves privadas ou segredos em variáveis VITE_*.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // necessário para o cookie HttpOnly de refresh token
})

/**
 * Request interceptor — injeta o access token no header Authorization.
 * O token é lido do store Zustand (memória), NUNCA do localStorage.
 */
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

let refreshEmAndamento: Promise<string | null> | null = null

/**
 * Troca o cookie de refresh por um novo access token.
 *
 * Chamadas concorrentes compartilham a mesma promise: o backend rotaciona o
 * refresh token a cada chamada, então dois POSTs simultâneos com o mesmo cookie
 * fariam o segundo falhar com o token já revogado pelo primeiro.
 *
 * Retorna o novo access token, ou null se a sessão não pôde ser renovada.
 */
export function refreshAccessToken(): Promise<string | null> {
  if (!refreshEmAndamento) {
    refreshEmAndamento = api
      .post<TokenResponse>('/auth/refresh')
      .then(({ data }) => {
        useAuthStore.getState().setAuth(data.access_token, data.user)
        return data.access_token
      })
      .catch(() => {
        useAuthStore.getState().clearAuth()
        limparQueriesDaSessao(queryClient)
        return null
      })
      .finally(() => {
        // Libera o cache para que uma expiração futura possa renovar de novo.
        refreshEmAndamento = null
      })
  }

  return refreshEmAndamento
}

/**
 * Response interceptor — renova a sessão de forma transparente.
 *
 * Em um 401 de rota protegida (access token expirado), tenta um refresh e
 * repete a request original uma única vez. Se o refresh falhar, a sessão acabou:
 * limpa o estado e manda para o login. Nunca registra token ou credencial em log.
 */
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RequestConfigComRetry | undefined
    const podeTentarRefresh =
      error.response?.status === 401 &&
      config !== undefined &&
      !config.jaTentouRefresh &&
      !ROTAS_SEM_REFRESH.some((rota) => config.url?.startsWith(rota))

    if (podeTentarRefresh) {
      config.jaTentouRefresh = true
      const novoToken = await refreshAccessToken()

      if (novoToken) {
        config.headers.Authorization = `Bearer ${novoToken}`
        return api(config)
      }

      redirecionarParaLogin()
    }

    return Promise.reject(error)
  },
)

function redirecionarParaLogin(): void {
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}
