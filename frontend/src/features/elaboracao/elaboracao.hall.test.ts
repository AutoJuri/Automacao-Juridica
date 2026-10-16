import { describe, expect, it } from 'vitest'

import { validarNovaElaboracao } from './elaboracao.form'
import { processoDeDadosManuais } from './elaboracao.manual'
import { juntarPorId } from './elaboracoes.pagina'
import type { ElaboracaoDetalhe, RascunhoManual } from './elaboracoes.types'
import { extrairDadosElaboracao } from './elaboracao.processo'
import { lerVersoesDaElaboracao } from './elaboracao.versoes'

const rascunho: RascunhoManual = {
  peca: 'contestacao',
  titulo: 'Peça avulsa',
  nu_processo: '0000001-00.2026.8.26.0100',
  parte_ativa: 'Autor',
  parte_passiva: 'Réu',
  classe: 'Procedimento Comum',
  assunto: 'Indenização',
  foro_vara: 'Foro Central',
  valor_causa: 'R$ 1.000,00',
  juiz: 'Juíza Ana',
}

function capa(parcial: Partial<ElaboracaoDetalhe> = {}): ElaboracaoDetalhe {
  return {
    id: 'elab-1',
    peca: 'contestacao',
    rotulo: 'Contestação',
    titulo: 'Peça avulsa',
    nu_processo: rascunho.nu_processo,
    autor: 'Autor',
    reu: 'Réu',
    tem_processo: false,
    updated_at: '2026-10-08T12:00:00Z',
    processo_id: null,
    manual: {
      titulo: rascunho.titulo,
      nu_processo: rascunho.nu_processo,
      parte_ativa: 'Autor',
      parte_passiva: 'Réu',
      classe: 'Procedimento Comum',
      assunto: 'Indenização',
      foro_vara: 'Foro Central',
      valor_causa: 'R$ 1.000,00',
      juiz: 'Juíza Ana',
    },
    ...parcial,
  }
}

describe('processoDeDadosManuais', () => {
  it('preenche os campos da capa e deixa as listas vazias', () => {
    const processo = processoDeDadosManuais(capa())
    const dados = extrairDadosElaboracao(processo)
    expect(dados.autor).toBe('Autor')
    expect(dados.reu).toBe('Réu')
    expect(dados.classe).toBe('Procedimento Comum')
    expect(dados.foroTribunal).toContain('Foro Central')
    expect(processo.movimentacoes).toEqual([])
    expect(processo.intimacoes).toEqual([])
    expect(processo.movimentacoes_status).toBe('indisponivel')
  })
})

describe('validarNovaElaboracao', () => {
  it('exige título', () => {
    const resultado = validarNovaElaboracao({ ...rascunho, titulo: '  ' })
    expect(resultado.ok).toBe(false)
    if (!resultado.ok) {
      expect(resultado.erros.titulo).toBeTruthy()
    }
  })

  it('aceita o rascunho mínimo', () => {
    expect(validarNovaElaboracao(rascunho).ok).toBe(true)
  })
})

describe('juntarPorId', () => {
  it('acrescenta a página seguinte sem repetir', () => {
    const junto = juntarPorId([
      [{ id: 'a' }, { id: 'b' }],
      [{ id: 'b' }, { id: 'c' }],
    ])
    expect(junto.map((item) => item.id)).toEqual(['a', 'b', 'c'])
  })
})

describe('lerVersoesDaElaboracao', () => {
  it('usa a chave antiga só quando a nova está vazia', () => {
    const armazenamento = new Map<string, string>([
      ['advogativa.minuta.versoes.proc-1.contestacao', JSON.stringify([{ id: 'v1', rotulo: 'Versão 1', criadoEm: '2026-10-08T00:00:00Z', html: '<p>oi</p>' }])],
    ])
    const fallback = lerVersoesDaElaboracao(
      (chave) => armazenamento.get(chave) ?? null,
      'elab-1',
      'proc-1',
      'contestacao',
    )
    expect(fallback).toHaveLength(1)

    armazenamento.set(
      'advogativa.minuta.versoes.elaboracao.elab-1',
      JSON.stringify([{ id: 'v2', rotulo: 'Versão 2', criadoEm: '2026-10-08T00:00:00Z', html: '<p>nova</p>' }]),
    )
    const atual = lerVersoesDaElaboracao(
      (chave) => armazenamento.get(chave) ?? null,
      'elab-1',
      'proc-1',
      'contestacao',
    )
    expect(atual[0]?.id).toBe('v2')
  })
})
