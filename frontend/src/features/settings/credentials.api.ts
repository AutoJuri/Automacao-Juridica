/**
 * Chamadas às rotas de credenciais do e-SAJ e conexão OAuth2 de e-mail.
 *
 * CPF e senha nunca voltam do backend — só a versão mascarada do CPF e um
 * booleano de status. O token OAuth2 do e-mail também nunca aparece aqui.
 */

import { api } from '#/lib/axios'
import type { AuthorizeUrlResponse, CredentialStatus, EmailProvider } from './credentials.types'

export interface SalvarCredencialEsajInput {
  cpf: string
  senha: string
}

export async function buscarStatusCredenciais(): Promise<CredentialStatus> {
  const { data } = await api.get<CredentialStatus>('/credentials/status')
  return data
}

export async function salvarCredencialEsaj(
  input: SalvarCredencialEsajInput,
): Promise<CredentialStatus> {
  const { data } = await api.post<CredentialStatus>('/credentials/esaj', input)
  return data
}

/** Dispara uma nova tentativa de login com a credencial já cadastrada. */
export async function revalidarCredencialEsaj(): Promise<CredentialStatus> {
  const { data } = await api.post<CredentialStatus>('/credentials/esaj/revalidar')
  return data
}

export async function removerCredencialEsaj(): Promise<CredentialStatus> {
  const { data } = await api.delete<CredentialStatus>('/credentials/esaj')
  return data
}

export async function desconectarEmail(): Promise<CredentialStatus> {
  const { data } = await api.delete<CredentialStatus>('/credentials/email')
  return data
}

/** Busca a URL de consentimento do provedor — o chamador navega até ela. */
export async function buscarUrlDeAutorizacaoEmail(
  provider: EmailProvider,
): Promise<AuthorizeUrlResponse> {
  const { data } = await api.get<AuthorizeUrlResponse>(`/credentials/email/${provider}/authorize`)
  return data
}
