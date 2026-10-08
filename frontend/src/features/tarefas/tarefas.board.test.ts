import { describe, expect, it } from 'vitest'

import {
  MAX_COLUNAS,
  adicionarColuna,
  ajustarTotais,
  atalhosDaColuna,
  incluirPagina,
  estaAtrasada,
  idDropColuna,
  moverTarefa,
  quadroInicial,
  removerColuna,
  renomearColuna,
  tarefasDaColuna,
  tomDaColuna,
  validarRascunho,
} from './tarefas.board'
import type { Quadro, Tarefa } from './tarefas.types'

function tarefa(parcial: Partial<Tarefa> & Pick<Tarefa, 'id' | 'colunaId'>): Tarefa {
  return {
    titulo: parcial.id,
    descricao: '',
    responsavelId: 'usuario-1',
    processoId: null,
    prazo: null,
    ...parcial,
  }
}

function quadroCom(tarefas: Tarefa[]): Quadro {
  return { ...quadroInicial(), tarefas }
}

describe('colunas', () => {
  it('começa com três colunas e nenhuma tarefa', () => {
    const quadro = quadroInicial()
    expect(quadro.colunas.map((coluna) => coluna.titulo)).toEqual([
      'A fazer',
      'Em andamento',
      'Concluído',
    ])
    expect(quadro.tarefas).toEqual([])
  })

  it('aceita a quarta coluna e recusa a quinta', () => {
    const comQuatro = adicionarColuna(quadroInicial(), '  Revisão  ', 'revisao')
    expect(comQuatro.colunas).toHaveLength(MAX_COLUNAS)
    expect(comQuatro.colunas[3]).toEqual({ id: 'revisao', titulo: 'Revisão', conclusao: false, total: 0 })
    expect(adicionarColuna(comQuatro, 'Extra', 'extra')).toBe(comQuatro)
  })

  it('renomeia com o texto limitado e ignora título vazio', () => {
    const quadro = quadroInicial()
    const renomeado = renomearColuna(quadro, 'a-fazer', '  Protocolar  ')
    expect(renomeado.colunas[0].titulo).toBe('Protocolar')
    expect(renomearColuna(renomeado, 'a-fazer', '   ')).toBe(renomeado)
  })

  it('remove só coluna vazia e preserva a última', () => {
    const quadro = quadroInicial()
    const semAndamento = removerColuna(quadro, 'em-andamento')
    expect(semAndamento.colunas.map((coluna) => coluna.id)).toEqual(['a-fazer', 'concluido'])

    const ocupada = quadroCom([tarefa({ id: 't1', colunaId: 'a-fazer' })])
    expect(removerColuna(ocupada, 'a-fazer')).toBe(ocupada)

    const uma = removerColuna(removerColuna(semAndamento, 'concluido'), 'a-fazer')
    expect(uma.colunas).toHaveLength(1)
    expect(removerColuna(uma, 'a-fazer')).toBe(uma)
  })
})

describe('moverTarefa', () => {
  it('reordena dentro da mesma coluna', () => {
    const quadro = quadroCom([
      tarefa({ id: 'a', colunaId: 'a-fazer' }),
      tarefa({ id: 'b', colunaId: 'a-fazer' }),
      tarefa({ id: 'c', colunaId: 'a-fazer' }),
    ])
    const paraBaixo = moverTarefa(quadro, 'a', 'c')
    expect(tarefasDaColuna(paraBaixo, 'a-fazer').map((item) => item.id)).toEqual(['b', 'c', 'a'])

    const paraCima = moverTarefa(quadro, 'c', 'a')
    expect(tarefasDaColuna(paraCima, 'a-fazer').map((item) => item.id)).toEqual(['c', 'a', 'b'])
  })

  it('move para outra coluna antes do card de destino', () => {
    const quadro = quadroCom([
      tarefa({ id: 'a', colunaId: 'a-fazer' }),
      tarefa({ id: 'b', colunaId: 'em-andamento' }),
      tarefa({ id: 'c', colunaId: 'em-andamento' }),
    ])
    const movido = moverTarefa(quadro, 'a', 'c')
    expect(tarefasDaColuna(movido, 'a-fazer')).toEqual([])
    expect(tarefasDaColuna(movido, 'em-andamento').map((item) => item.id)).toEqual(['b', 'a', 'c'])
  })

  it('solta em coluna vazia e ignora alvo inexistente', () => {
    const quadro = quadroCom([tarefa({ id: 'a', colunaId: 'a-fazer' })])
    const movido = moverTarefa(quadro, 'a', idDropColuna('concluido'))
    expect(tarefasDaColuna(movido, 'concluido').map((item) => item.id)).toEqual(['a'])
    expect(tarefasDaColuna(movido, 'a-fazer')).toEqual([])

    expect(moverTarefa(quadro, 'a', idDropColuna('nao-existe'))).toBe(quadro)
    expect(moverTarefa(quadro, 'fantasma', 'a')).toBe(quadro)
    expect(moverTarefa(quadro, 'a', 'a')).toBe(quadro)
  })
})

describe('atalhos do card', () => {
  it('em "a fazer" oferece a próxima coluna e o salto para concluído', () => {
    const quadro = quadroInicial()
    expect(atalhosDaColuna(quadro, 'a-fazer')).toEqual({
      avancar: { id: 'em-andamento', titulo: 'Em andamento' },
      concluir: { id: 'concluido', titulo: 'Concluído' },
    })
  })

  it('na coluna anterior à conclusão só oferece concluir', () => {
    const quadro = quadroInicial()
    expect(atalhosDaColuna(quadro, 'em-andamento')).toEqual({
      avancar: null,
      concluir: { id: 'concluido', titulo: 'Concluído' },
    })
    expect(atalhosDaColuna(quadro, 'concluido')).toEqual({ avancar: null, concluir: null })
  })

  it('avança para a coluna do meio e ainda deixa saltar a conclusão', () => {
    const quadro = adicionarColuna(quadroInicial(), 'Revisão', 'revisao')
    const ordem = ['a-fazer', 'revisao', 'em-andamento', 'concluido']
    const reordenado = {
      ...quadro,
      colunas: ordem.map((id) => quadro.colunas.find((coluna) => coluna.id === id)!),
    }
    expect(atalhosDaColuna(reordenado, 'a-fazer')).toEqual({
      avancar: { id: 'revisao', titulo: 'Revisão' },
      concluir: { id: 'concluido', titulo: 'Concluído' },
    })
    expect(atalhosDaColuna(reordenado, 'em-andamento')).toEqual({
      avancar: null,
      concluir: { id: 'concluido', titulo: 'Concluído' },
    })
  })

  it('ignora coluna que não está no quadro', () => {
    expect(atalhosDaColuna(quadroInicial(), 'fantasma')).toEqual({ avancar: null, concluir: null })
  })
})

describe('página da conclusão', () => {
  it('soma o destino e acrescenta só o card que ainda não está na tela', () => {
    const quadro = quadroCom([tarefa({ id: 'a', colunaId: 'concluido' })])
    const movido = ajustarTotais(
      { ...quadro, tarefas: [tarefa({ id: 'a', colunaId: 'a-fazer' })] },
      'concluido',
      'a-fazer',
    )
    expect(movido.colunas.find((coluna) => coluna.id === 'concluido')?.total).toBe(0)
    expect(movido.colunas.find((coluna) => coluna.id === 'a-fazer')?.total).toBe(1)

    const comPagina = incluirPagina(quadro, 'concluido', [tarefa({ id: 'a', colunaId: 'concluido' }), tarefa({ id: 'b', colunaId: 'concluido' })], 12)
    expect(comPagina.tarefas.map((item) => item.id)).toEqual(['a', 'b'])
    expect(comPagina.colunas.find((coluna) => coluna.id === 'concluido')?.total).toBe(12)
  })
})

describe('cor da coluna', () => {
  it('pinta a primeira de azul, o meio de âmbar e a conclusão de verde', () => {
    const { colunas } = quadroInicial()
    expect(colunas.map((coluna) => tomDaColuna(colunas, coluna))).toEqual([
      'fazer',
      'andamento',
      'conclusao',
    ])
  })

  it('trata coluna extra no meio como andamento', () => {
    const quadro = adicionarColuna(quadroInicial(), 'Revisão', 'revisao')
    const extra = quadro.colunas.find((coluna) => coluna.id === 'revisao')!
    expect(tomDaColuna(quadro.colunas, extra)).toBe('andamento')
  })
})

describe('prazo e rascunho', () => {
  it('marca atraso só quando a data é anterior a hoje', () => {
    expect(estaAtrasada('2026-10-01', '2026-10-02')).toBe(true)
    expect(estaAtrasada('2026-10-02', '2026-10-02')).toBe(false)
    expect(estaAtrasada(null, '2026-10-02')).toBe(false)
    expect(estaAtrasada('amanha', '2026-10-02')).toBe(false)
  })

  it('recusa título vazio e responsável ausente', () => {
    expect(
      validarRascunho({
        titulo: '  ',
        descricao: '',
        responsavelId: 'usuario-1',
        processoId: null,
        prazo: null,
      }),
    ).toBe('Informe o título da tarefa.')
    expect(
      validarRascunho({
        titulo: 'Protocolar',
        descricao: '',
        responsavelId: '',
        processoId: null,
        prazo: null,
      }),
    ).toBe('Escolha quem vai fazer a tarefa.')
  })
})
