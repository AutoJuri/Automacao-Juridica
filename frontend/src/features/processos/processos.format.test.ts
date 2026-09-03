import { describe, expect, it } from 'vitest'

import {
  escapeHtml,
  formatarNumeroCnj,
  juntarLocalProcesso,
  rotuloGrau,
  rotuloPortal,
  rotuloTribunal,
  tagTribunalGrau,
} from './processos.format'

describe('formatarNumeroCnj', () => {
  it('formata 20 digitos no padrao CNJ', () => {
    expect(formatarNumeroCnj('10025618420268260100')).toBe('1002561-84.2026.8.26.0100')
  })

  it('normaliza numero ja pontuado', () => {
    expect(formatarNumeroCnj('1002561-84.2026.8.26.0100')).toBe(
      '1002561-84.2026.8.26.0100',
    )
  })

  it('nao inventa formato quando nao ha 20 digitos', () => {
    expect(formatarNumeroCnj('123')).toBe('123')
    expect(formatarNumeroCnj('')).toBe('Número não informado')
    expect(formatarNumeroCnj(null)).toBe('Número não informado')
  })
})

describe('rotulos de tribunal e instancia', () => {
  it('mapeia e-SAJ TJSP e primeiro grau', () => {
    expect(rotuloTribunal('esaj_tjsp')).toBe('TJSP')
    expect(rotuloPortal('esaj_tjsp')).toBe('e-SAJ')
    expect(rotuloGrau('PG')).toBe('1º Grau')
    expect(tagTribunalGrau('esaj_tjsp', 'PG')).toBe('TJSP · 1º Grau')
  })

  it('mapeia segundo grau', () => {
    expect(rotuloGrau('sg')).toBe('2º Grau')
    expect(tagTribunalGrau('esaj_tjsp', 'SG')).toBe('TJSP · 2º Grau')
  })

  it('omite grau quando a instancia nao veio', () => {
    expect(rotuloGrau(null)).toBeNull()
    expect(tagTribunalGrau('esaj_tjsp', null)).toBe('TJSP')
  })
})

describe('juntarLocalProcesso', () => {
  it('junta foro area e vara com traco', () => {
    expect(juntarLocalProcesso('Foro Central Cível', 'Cível', '12ª Vara')).toBe(
      'Foro Central Cível - Cível - 12ª Vara',
    )
  })

  it('omite trechos vazios', () => {
    expect(juntarLocalProcesso('Foro Central', '', '1ª Vara')).toBe(
      'Foro Central - 1ª Vara',
    )
    expect(juntarLocalProcesso('', '', '')).toBe('')
  })
})

describe('escapeHtml', () => {
  it('escapa markup para nao executar html de terceiros', () => {
    expect(escapeHtml('<img src=x onerror=alert(1)>')).toBe(
      '&lt;img src=x onerror=alert(1)&gt;',
    )
  })
})
