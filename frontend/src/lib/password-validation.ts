/**
 * Regras de senha compartilhadas entre schemas de formulário (auth e
 * credenciais do e-SAJ) — espelha `backend/app/core/validators.py`.
 */

export const SENHA_MIN = 8
/** Teto do bcrypt: acima de 72 bytes a cauda da senha seria ignorada. */
export const SENHA_MAX = 72

/**
 * `.max(72)` do Zod conta caracteres, mas o teto do bcrypt é em bytes UTF-8 —
 * um emoji ou acento pode ocupar de 2 a 4 bytes. Sem este check, uma senha
 * com 72 caracteres multibyte passaria no frontend e só seria rejeitada pelo
 * 422 do backend, numa UX pior.
 */
export function cabeEmBytesDoBcrypt(senha: string): boolean {
  return new TextEncoder().encode(senha).length <= SENHA_MAX
}
