import { describe, expect, it } from 'vitest'

import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import {
  completudeDadosProcesso,
  extrairDadosElaboracao,
  montarEnderecamento,
} from './elaboracao.processo'

function processoBase(overrides: Partial<ProcessoDetalhe> = {}): ProcessoDetalhe {
  return {
    id: 'proc-1',
    tribunal: 'esaj_tjsp',
    nu_processo: '0009189-43.2026.8.26.0114',
    de_classe: 'Cumprimento de sentença',
    de_assunto: 'Serviços Hospitalares',
    instancia: 'PG',
    parte_ativa: { nome: 'Aurelio Agostinho Ruete', representada: false },
    parte_passiva: { nome: 'BRADESCO SAÚDE S/A', representada: true },
    last_synced_at: null,
    ultima_atividade: null,
    fixado: false,
    url_cpo: null,
    url_pasta: null,
    foro: 'Foro de Campinas',
    vara: '1ª Vara Cível',
    juiz: null,
    distribuicao: null,
    controle: null,
    area: 'Cível',
    valor_acao: 'R$ 10.000,00',
    partes_cpo: [],
    intimacoes: [],
    audiencias: [],
    movimentacoes: [],
    peticoes_diversas: [],
    audiencias_cpo: [],
    movimentacoes_status: 'ok',
    sem_incidentes: null,
    sem_apensos: null,
    ...overrides,
  }
}

describe('extrairDadosElaboracao', () => {
  it('preenche CNJ, polos, foro e valor reais', () => {
    const dados = extrairDadosElaboracao(processoBase())
    expect(dados.cnj).toBe('0009189-43.2026.8.26.0114')
    expect(dados.autor).toBe('Aurelio Agostinho Ruete')
    expect(dados.reu).toBe('BRADESCO SAÚDE S/A')
    expect(dados.foroTribunal).toContain('Foro de Campinas')
    expect(dados.foroTribunal).toContain('TJSP')
    expect(dados.valorCausa).toBe('R$ 10.000,00')
  })

  it('nao inventa valor quando o CPO nao trouxe', () => {
    const dados = extrairDadosElaboracao(processoBase({ valor_acao: null, juiz: null }))
    expect(dados.valorCausa).toBe('Não disponível')
    expect(dados.juiz).toBe('Não disponível')
  })
})

describe('completudeDadosProcesso', () => {
  it('conta so campos realmente preenchidos', () => {
    const resultado = completudeDadosProcesso(processoBase({ juiz: null }))
    expect(resultado.total).toBe(7)
    expect(resultado.atendidos).toBe(6)
    expect(resultado.percentual).toBe(86)
    expect(resultado.itens.find((item) => item.id === 'juiz')?.preenchido).toBe(false)
  })
})

describe('montarEnderecamento', () => {
  it('usa vara e foro reais em maiusculas', () => {
    expect(montarEnderecamento(processoBase())).toBe(
      'EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL DO FORO DE CAMPINAS',
    )
  })

  it('nao inventa vara quando o CPO nao trouxe', () => {
    expect(montarEnderecamento(processoBase({ vara: null, foro: null }))).toBe(
      'EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO',
    )
  })
})
