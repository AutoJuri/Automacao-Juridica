import { describe, expect, it } from 'vitest'

import {
  SECOES_LATERAL,
  SECOES_TOPO,
  estaEmGerencias,
  secaoTopoAtiva,
} from './nav.constants'

describe('SECOES_LATERAL', () => {
  it('usa os labels operacionais curtos e as rotas já existentes', () => {
    expect(SECOES_LATERAL.map((item) => [item.to, item.label])).toEqual([
      ['/', 'Andamentos'],
      ['/consulta-pasta', 'Consultas'],
      ['/pautas', 'Audiências'],
      ['/push-robos', 'Push Robôs'],
    ])
  })
})

describe('SECOES_TOPO', () => {
  it('lista as áreas da navbar; Gerências abre Andamentos', () => {
    expect(SECOES_TOPO.map((item) => [item.to, item.label])).toEqual([
      ['/', 'Gerências'],
      ['/elaboracoes', 'Elaborações'],
      ['/drive', 'Drive'],
      ['/tarefas', 'Tarefas'],
    ])
  })
})

describe('estaEmGerencias', () => {
  it('vale nas seções operacionais e não nas outras áreas', () => {
    expect(estaEmGerencias('/')).toBe(true)
    expect(estaEmGerencias('/consulta-pasta')).toBe(true)
    expect(estaEmGerencias('/elaboracoes')).toBe(false)
    expect(estaEmGerencias('/configuracoes')).toBe(false)
  })
})

describe('secaoTopoAtiva', () => {
  it('marca Gerências em qualquer seção operacional', () => {
    expect(secaoTopoAtiva('/', '/')).toBe(true)
    expect(secaoTopoAtiva('/', '/pautas')).toBe(true)
    expect(secaoTopoAtiva('/', '/drive')).toBe(false)
  })

  it('marca Elaborações na lista e na minuta de um processo', () => {
    expect(secaoTopoAtiva('/elaboracoes', '/elaboracoes')).toBe(true)
    expect(secaoTopoAtiva('/elaboracoes', '/elaboracao/abc-123')).toBe(true)
    expect(secaoTopoAtiva('/elaboracoes', '/')).toBe(false)
  })
})
