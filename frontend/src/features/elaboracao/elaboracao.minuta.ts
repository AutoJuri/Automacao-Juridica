import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { extrairDadosElaboracao, montarEnderecamento } from './elaboracao.processo'

/** Escapa texto do e-SAJ antes de montar HTML da minuta (TipTap). */
export function escaparHtml(texto: string): string {
  return texto
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

/**
 * Estrutura da minuta com cabeçalho real. O corpo jurídico é placeholder —
 * não inventa fatos, teses nem jurisprudência.
 */
export function montarHtmlMinuta(processo: ProcessoDetalhe, pecaNome: string): string {
  const dados = extrairDadosElaboracao(processo)
  const e = escaparHtml
  const peca = e(pecaNome)
  const cnj = e(dados.cnj)
  const autor = e(dados.autor)
  const reu = e(dados.reu)
  const classe = e(dados.classe)
  const valor = e(dados.valorCausa)
  const enderecamento = e(montarEnderecamento(processo))
  const local = dados.local !== 'Não disponível' ? e(dados.local) : ''

  return [
    `<p style="text-align: center"><strong>${enderecamento}</strong></p>`,
    '<p></p>',
    `<p>Processo nº: ${cnj}</p>`,
    `<p>Classe: ${classe}</p>`,
    `<p>Autor: ${autor}</p>`,
    `<p>Réu: ${reu}</p>`,
    '<p></p>',
    `<p>${reu}, vem, respeitosamente, à presença de Vossa Excelência, apresentar <strong>${peca}</strong> em face de ${autor}.</p>`,
    '<p>O cabeçalho acima usa dados reais do e-SAJ. O texto jurídico das seções seguintes ainda não é gerado — edite livremente ou aguarde a elaboração por IA.</p>',
    '<p></p>',
    '<p><strong>I. DOS FATOS</strong></p>',
    '<p>A narrativa dos fatos será redigida quando a elaboração estiver em operação.</p>',
    '<p></p>',
    '<p><strong>II. PRELIMINARMENTE</strong></p>',
    '<p>As preliminares serão redigidas quando a elaboração estiver em operação.</p>',
    '<p></p>',
    '<p><strong>III. DO DIREITO</strong></p>',
    '<p>Os fundamentos jurídicos serão redigidos quando a elaboração estiver em operação.</p>',
    '<p></p>',
    '<p><strong>IV. DOS PEDIDOS</strong></p>',
    '<p>Os pedidos finais serão redigidos quando a elaboração estiver em operação.</p>',
    '<p></p>',
    `<p>Valor da Causa: ${valor}.</p>`,
    '<p>Termos em que, pede deferimento.</p>',
    local ? `<p>${local}.</p>` : '',
  ]
    .filter(Boolean)
    .join('')
}

export const FONTES_MINUTA = [
  { valor: 'Times New Roman, Times, serif', rotulo: 'Times New Roman' },
  { valor: 'Arial, Helvetica, sans-serif', rotulo: 'Arial' },
  { valor: 'Calibri, Carlito, sans-serif', rotulo: 'Calibri' },
  { valor: 'Garamond, "Palatino Linotype", serif', rotulo: 'Garamond' },
  { valor: 'Inter, system-ui, sans-serif', rotulo: 'Inter' },
] as const

export const TAMANHOS_MINUTA = [
  { valor: '10pt', rotulo: '10 pt' },
  { valor: '11pt', rotulo: '11 pt' },
  { valor: '12pt', rotulo: '12 pt (Padrão)' },
  { valor: '14pt', rotulo: '14 pt' },
  { valor: '18pt', rotulo: '18 pt' },
] as const

export const ESPACAMENTOS_MINUTA = [
  { valor: '1', rotulo: '1.0 (Simples)' },
  { valor: '1.15', rotulo: '1.15' },
  { valor: '1.5', rotulo: '1.5 (Padrão Jurídico)' },
  { valor: '2', rotulo: '2.0 (Duplo)' },
] as const

export const ACOES_GRIFO = [
  { id: 'incisivo', rotulo: 'Tornar mais incisivo' },
  { id: 'fundamentacao', rotulo: 'Adicionar fundamentação' },
  { id: 'resumir', rotulo: 'Resumir trecho' },
  { id: 'gramatica', rotulo: 'Corrigir gramática' },
] as const
