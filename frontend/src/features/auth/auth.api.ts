/**
 * Chamadas às rotas de autenticação do backend.
 *
 * O refresh token vive em cookie HttpOnly — nenhuma função aqui o manipula,
 * o navegador o envia automaticamente porque a instância do axios usa
 * `withCredentials: true`.
 */

import { api } from '#/lib/axios'
import type { AuthUser } from '#/store/auth.store'
import type { MessageResponse, TokenResponse } from './auth.types'

export interface CadastroInput {
  name: string
  email: string
  password: string
}

export interface LoginInput {
  email: string
  password: string
}

export async function cadastrar(input: CadastroInput): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/cadastro', input)
  return data
}

export async function login(input: LoginInput): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', input)
  return data
}

/** Revoga o refresh token no banco e limpa o cookie do navegador. */
export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

/**
 * Dispara o envio do link de redefinição.
 * A resposta é sempre a mesma, exista o e-mail ou não — o backend não permite
 * descobrir quais e-mails estão cadastrados.
 */
export async function recuperarSenha(email: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/auth/recuperar-senha', { email })
  return data
}

export async function redefinirSenha(token: string, novaSenha: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/auth/redefinir-senha', {
    token,
    new_password: novaSenha,
  })
  return data
}

/** Dados do usuário autenticado. Requer access token válido. */
export async function buscarUsuarioAtual(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>('/auth/me')
  return data
}
