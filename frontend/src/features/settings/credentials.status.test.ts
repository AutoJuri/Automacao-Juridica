import { describe, expect, it } from 'vitest'

import {
  deveFazerPolling,
  POLL_GRACA_INICIO_MS,
  POLL_MAX_MS,
} from './credentials.status'
import type { CredentialStatus } from './credentials.types'

function dados(
  parcial: Partial<Pick<CredentialStatus, 'cadastrado' | 'session_status' | 'validacao_em_andamento'>>,
) {
  return {
    cadastrado: true,
    session_status: 'reauth_pendente' as const,
    validacao_em_andamento: false,
    ...parcial,
  }
}

describe('deveFazerPolling', () => {
  it('nao faz polling em reauth_pendente orfao (sem Playwright e sem disparo recente)', () => {
    expect(deveFazerPolling(dados({}), null, 10_000)).toBe(false)
  })

  it('faz polling enquanto o Playwright esta rodando', () => {
    expect(
      deveFazerPolling(dados({ validacao_em_andamento: true }), null, 10_000),
    ).toBe(true)
  })

  it('faz polling na janela de graca depois do POST que disparou a validacao', () => {
    expect(deveFazerPolling(dados({}), 0, POLL_GRACA_INICIO_MS - 1)).toBe(true)
    expect(deveFazerPolling(dados({}), 0, POLL_GRACA_INICIO_MS)).toBe(false)
  })

  it('para o polling depois do teto mesmo com Playwright ainda marcado', () => {
    expect(
      deveFazerPolling(dados({ validacao_em_andamento: true }), 0, POLL_MAX_MS + 1),
    ).toBe(false)
  })

  it('nao faz polling em status terminal', () => {
    expect(
      deveFazerPolling(dados({ session_status: 'ativo', validacao_em_andamento: true }), 0, 1000),
    ).toBe(false)
  })
})
