import { describe, expect, it } from 'vitest'

import {
  avisoStatus,
  deveAcompanhar,
  etapaPreparacao,
  notaElaborar,
  percentualLeitura,
  rotuloBotao,
  rotuloDocumento,
  rotuloFaixaAutos,
  temSemAcesso,
  textoDoRoteiro,
  textoProgresso,
} from './dossie.estado'

describe('dossie.estado', () => {
  it('mostra o progresso e acompanha só enquanto lê', () => {
    expect(textoProgresso(12, 30)).toBe('12 de 30 documentos')
    expect(deveAcompanhar('lendo')).toBe(true)
    expect(deveAcompanhar('pronto')).toBe(false)
    expect(deveAcompanhar(undefined)).toBe(false)
  })

  it('nomeia o botão conforme o que ainda falta', () => {
    expect(rotuloBotao('ocioso', 0, 4)).toBe('Ler autos')
    expect(rotuloBotao('lendo', 1, 4)).toBe('Lendo autos…')
    expect(rotuloBotao('pronto', 2, 4)).toBe('Continuar leitura')
    expect(rotuloBotao('pronto', 4, 4)).toBe('Ler de novo')
  })

  it('avisa o Elaborar quando o resumo existe', () => {
    expect(notaElaborar('ocioso', null)).toBe(
      'Autos ainda não lidos. O Elaborar não verá a pasta.',
    )
    expect(notaElaborar('pronto', '21/10/2026 12:00')).toContain('21/10/2026 12:00')
    expect(notaElaborar('lendo', null)).toContain('em andamento')
  })

  it('não esconde senha dos autos nem sessão expirada', () => {
    expect(rotuloDocumento('sem_acesso')).toBe('Sem acesso')
    expect(rotuloDocumento('ilegivel')).toBe('Ilegível')
    expect(temSemAcesso(['lido', 'sem_acesso'])).toBe(true)
    expect(avisoStatus('sessao_expirada')).toContain('Configurações')
    expect(avisoStatus('bloqueado')).toContain('cookie')
    expect(avisoStatus('pronto')).toBeNull()
  })

  it('resume a faixa e aponta a etapa que ainda falta', () => {
    expect(percentualLeitura(0, 0)).toBe(0)
    expect(percentualLeitura(1, 4)).toBe(25)
    expect(rotuloFaixaAutos('lendo', 1, 4)).toBe('Lendo autos')
    expect(rotuloFaixaAutos('ocioso', 0, 0)).toBe('Autos não lidos')
    expect(rotuloFaixaAutos('pronto', 4, 4)).toBe('Autos lidos')
    expect(etapaPreparacao('ocioso', 0, 0, false, false)).toBe(1)
    expect(etapaPreparacao('pronto', 4, 4, false, false)).toBe(2)
    expect(etapaPreparacao('pronto', 4, 4, true, false)).toBe(3)
    expect(etapaPreparacao('pronto', 4, 4, true, true)).toBe(5)
    expect(etapaPreparacao('erro', 0, 60, false, false)).toBe(1)
    expect(etapaPreparacao('erro', 0, 60, true, false)).toBe(3)
  })

  it('junta o roteiro sem estourar o limite da minuta', () => {
    const texto = textoDoRoteiro({
      resumo: 'Resumo do processo.',
      tese: 'Ilegitimidade.',
      pedidos: 'Improcedência.',
      acrescentar: '',
      nao_incluir: 'Não citar acordo.',
      jurisprudencia: 'Ementa colada.',
    })
    expect(texto).toContain('Tese:\nIlegitimidade.')
    expect(texto).toContain('Jurisprudência colada pelo advogado:')
    expect(texto).not.toContain('Pontos a acrescentar')
    expect(texto.length).toBeLessThanOrEqual(8000)
  })
})
