import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

import { useAuthStore } from '#/store/auth.store'

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

/**
 * Response interceptor — trata erros de autenticação.
 * Em caso de 401, limpa o estado de auth e redireciona para /login.
 * Nunca registra o token ou detalhes de credenciais nos logs.
 */
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearAuth()
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)
