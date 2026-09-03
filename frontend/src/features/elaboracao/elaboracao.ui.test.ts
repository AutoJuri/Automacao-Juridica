import { describe, expect, it } from 'vitest'

import { alinhamentoDoNo, posicaoPainelGrifo, validarArquivoModelo } from './elaboracao.ui'
import { adicionarVersao, lerVersoes } from './elaboracao.versoes'

describe('posicaoPainelGrifo', () => {
  const viewport = { width: 1280, height: 800 }
  const painel = { width: 448, height: 300 }

  it('abre abaixo quando ha espaco', () => {
    const pos = posicaoPainelGrifo(
      { top: 120, bottom: 140, left: 400 },
      viewport,
      painel,
    )
    expect(pos.acima).toBe(false)
    expect(pos.top).toBe(148)
    expect(pos.bottom).toBeNull()
  })

  it('ancora a base do painel perto da selecao no rodape', () => {
    const pos = posicaoPainelGrifo(
      { top: 720, bottom: 760, left: 400 },
      viewport,
      painel,
    )
    expect(pos.acima).toBe(true)
    expect(pos.top).toBeNull()
    expect(pos.bottom).toBe(88)
  })
})

describe('alinhamentoDoNo', () => {
  it('respeita left e ignora valor invalido', () => {
    expect(alinhamentoDoNo('left')).toBe('left')
    expect(alinhamentoDoNo('justify')).toBe('justify')
    expect(alinhamentoDoNo(undefined)).toBe('justify')
  })
})

describe('validarArquivoModelo', () => {
  it('aceita txt pequeno', () => {
    expect(validarArquivoModelo({ name: 'tese.txt', size: 1200 })).toBeNull()
  })

  it('rejeita extensao e arquivo grande', () => {
    expect(validarArquivoModelo({ name: 'foto.png', size: 10 })).toMatch(/TXT/)
    expect(validarArquivoModelo({ name: 'a.pdf', size: 6 * 1024 * 1024 })).toMatch(/5 MB/)
  })
})

describe('versoes da minuta', () => {
  it('ignora json invalido', () => {
    expect(lerVersoes('nao-json')).toEqual([])
    expect(lerVersoes('[]')).toEqual([])
  })

  it('empilha versao nova no topo', () => {
    const lista = adicionarVersao([], '<p>a</p>', new Date('2026-09-02T15:00:00.000Z'))
    expect(lista).toHaveLength(1)
    expect(lista[0].rotulo).toBe('Versão 1')
    expect(lista[0].html).toBe('<p>a</p>')
    const duas = adicionarVersao(lista, '<p>b</p>', new Date('2026-09-02T16:00:00.000Z'))
    expect(duas[0].rotulo).toBe('Versão 2')
    expect(duas[1].html).toBe('<p>a</p>')
  })
})
