import { describe, expect, it } from 'vitest'

import { textoCampoCpo } from './processos.dates'

describe('textoCampoCpo', () => {
  it('prioriza o valor do portal', () => {
    expect(textoCampoCpo('  Foro Central  ', true)).toBe('Foro Central')
  })

  it('diz que ainda nao buscou quando o CPO esta pendente', () => {
    expect(textoCampoCpo(null, true)).toBe('Ainda não buscado no CPO')
    expect(textoCampoCpo('  ', true)).toBe('Ainda não buscado no CPO')
  })

  it('nao inventa valor depois do sync', () => {
    expect(textoCampoCpo(null, false)).toBe('Não disponível')
  })
})
