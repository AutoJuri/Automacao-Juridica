/**
 * Contratos de resposta das rotas de credenciais, espelhando os schemas
 * Pydantic do backend (backend/app/schemas/credentials.py).
 */

export type EmailProvider = 'gmail' | 'outlook'

/** Espelha `SESSION_STATUSES` em `backend/app/models/tribunal.py`. */
export type SessionStatus =
  | 'ativo'
  | 'reauth_pendente'
  | 'bloqueado'
  | 'credencial_invalida'
  | 'email_desconectado'
  | 'portal_indisponivel'
  | 'codigo_nao_encontrado'

export interface CredentialStatus {
  cadastrado: boolean
  tribunal: string | null
  cpf_mascarado: string | null
  email_provider: EmailProvider | null
  email_conectado: boolean
  last_validated_at: string | null
  is_active: boolean | null
  session_status: SessionStatus | null
  /** `status=ativo` mas o cookie já passou do `expires_at` (ou sumiu). */
  sessao_expirada: boolean
  /**
   * Playwright deste processo está rodando agora. Distinto de
   * `session_status === 'reauth_pendente'`, que também significa
   * "cookie inválido, falta revalidar".
   */
  validacao_em_andamento: boolean
}

export interface AuthorizeUrlResponse {
  authorize_url: string
}

/**
 * Sugestão de provedor por domínio do e-mail de login (Etapa 9) — nunca
 * decide sozinha, só simplifica o card de conexão. `null` = sem sugestão
 * (a UI mantém a escolha manual).
 */
export interface ProviderSugerido {
  provider: EmailProvider | null
}
