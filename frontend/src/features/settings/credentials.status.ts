import type { CredentialStatus } from './credentials.types'

export const POLL_INTERVALO_MS = 3000
/** Folga além dos 60s de `TIMEOUT_VALIDACAO_SEGUNDOS` no backend. */
export const POLL_MAX_MS = 90_000
/** Janela entre o POST que dispara a BackgroundTask e o Playwright entrar no set. */
export const POLL_GRACA_INICIO_MS = 15_000

export function deveFazerPolling(
  dados: Pick<CredentialStatus, 'cadastrado' | 'session_status' | 'validacao_em_andamento'> | undefined,
  disparadoEm: number | null,
  agora: number,
): boolean {
  if (!dados?.cadastrado || dados.session_status !== 'reauth_pendente') {
    return false
  }
  if (dados.validacao_em_andamento) {
    return disparadoEm === null || agora - disparadoEm <= POLL_MAX_MS
  }
  return disparadoEm !== null && agora - disparadoEm < POLL_GRACA_INICIO_MS
}
