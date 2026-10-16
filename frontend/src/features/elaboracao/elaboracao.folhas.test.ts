import { describe, expect, it } from 'vitest'

import { distribuirEmFolhas } from './elaboracao.folhas'

const ALTURA = 100

describe('distribuirEmFolhas', () => {
  it('começa com uma folha mesmo sem texto', () => {
    expect(distribuirEmFolhas([], ALTURA)).toEqual({
      quebras: [],
      paginas: 1,
      sobra: ALTURA,
    })
  })

  it('mantém na mesma folha o que ainda cabe', () => {
    const resultado = distribuirEmFolhas(
      [
        { pos: 1, altura: 40, forcarQuebra: false },
        { pos: 8, altura: 40, forcarQuebra: false },
      ],
      ALTURA,
    )
    expect(resultado.paginas).toBe(1)
    expect(resultado.quebras).toEqual([])
    expect(resultado.sobra).toBe(20)
  })

  it('abre outra folha quando a linha não cabe', () => {
    const resultado = distribuirEmFolhas(
      [
        { pos: 1, altura: 80, forcarQuebra: false },
        { pos: 20, altura: 40, forcarQuebra: false },
      ],
      ALTURA,
    )
    expect(resultado.paginas).toBe(2)
    expect(resultado.quebras).toEqual([{ pos: 20, restante: 20 }])
    expect(resultado.sobra).toBe(60)
  })

  it('quebra de página abre uma folha mesmo com espaço sobrando', () => {
    const resultado = distribuirEmFolhas(
      [
        { pos: 1, altura: 20, forcarQuebra: false },
        { pos: 10, altura: 0, forcarQuebra: true },
        { pos: 12, altura: 20, forcarQuebra: false },
      ],
      ALTURA,
    )
    expect(resultado.paginas).toBe(2)
    expect(resultado.quebras).toEqual([{ pos: 10, restante: 80 }])
  })

  it('duas quebras seguidas criam uma folha em branco no meio', () => {
    const resultado = distribuirEmFolhas(
      [
        { pos: 1, altura: 0, forcarQuebra: true },
        { pos: 3, altura: 0, forcarQuebra: true },
      ],
      ALTURA,
    )
    expect(resultado.paginas).toBe(3)
    expect(resultado.quebras.map((quebra) => quebra.pos)).toEqual([1, 3])
  })
})
