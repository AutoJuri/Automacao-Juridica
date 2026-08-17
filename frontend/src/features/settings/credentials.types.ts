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
}

export interface AuthorizeUrlResponse {
  authorize_url: string
}
