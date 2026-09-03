import { describe, expect, it } from 'vitest'

import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { escaparHtml, montarHtmlMinuta } from './elaboracao.minuta'

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

describe('escaparHtml', () => {
  it('escapa tags para nao injetar HTML do scraping', () => {
    expect(escaparHtml('<img src=x onerror=alert(1)>')).toBe(
      '&lt;img src=x onerror=alert(1)&gt;',
    )
  })
})

describe('montarHtmlMinuta', () => {
  it('usa CNJ, polos e peca reais e nao inventa tese', () => {
    const html = montarHtmlMinuta(processoBase(), 'Contestação')
    expect(html).toContain('0009189-43.2026.8.26.0114')
    expect(html).toContain('Aurelio Agostinho Ruete')
    expect(html).toContain('BRADESCO SAÚDE S/A')
    expect(html).toContain('Contestação')
    expect(html).toContain('ainda não é gerado')
    expect(html).not.toContain('REsp')
  })

  it('escapa nome de parte com caracteres HTML', () => {
    const html = montarHtmlMinuta(
      processoBase({
        parte_ativa: { nome: 'Silva <script>', representada: false },
      }),
      'Réplica',
    )
    expect(html).toContain('Silva &lt;script&gt;')
    expect(html).not.toContain('<script>')
  })
})
