import { describe, expect, it } from 'vitest'

import { destinoConvite, tokenDoDestino } from './organizations.redirect'

const TOKEN = '11111111-1111-4111-8111-111111111111'

describe('destinoConvite', () => {
  it('aceita só o caminho do convite com uuid', () => {
    expect(destinoConvite(`/convite/${TOKEN}`)).toBe(`/convite/${TOKEN}`)
    expect(tokenDoDestino(`/convite/${TOKEN}`)).toBe(TOKEN)
  })

  it('recusa redirect externo ou caminho arbitrário', () => {
    expect(destinoConvite(undefined)).toBeNull()
    expect(destinoConvite('')).toBeNull()
    expect(destinoConvite('/')).toBeNull()
    expect(destinoConvite('/configuracoes')).toBeNull()
    expect(destinoConvite('//evil.example/convite/' + TOKEN)).toBeNull()
    expect(destinoConvite('https://evil.example/convite/' + TOKEN)).toBeNull()
    expect(destinoConvite(`/convite/${TOKEN}/extra`)).toBeNull()
    expect(destinoConvite('/convite/nao-e-uuid')).toBeNull()
  })
})
