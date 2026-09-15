import type { FocusEvent } from 'react'

export const GRIFO_PAINEL_ALTURA = 300
export const GRIFO_PAINEL_LARGURA = 448
export const GRIFO_PAINEL_FOLGA = 8

/** Classe CSS em styles.css — o mesmo azul dos botões e ícones. */
export const FOCO_CAMPO = 'foco-campo'

export const propsFocoCampo = {
  onFocus: (e: FocusEvent<HTMLElement>) => {
    e.currentTarget.setAttribute('data-foco', '')
  },
  onBlur: (e: FocusEvent<HTMLElement>) => {
    e.currentTarget.removeAttribute('data-foco')
  },
}

export type AlinhamentoMinuta = 'left' | 'center' | 'right' | 'justify'

/** Lê o alinhamento do parágrafo no cursor — isActive('justify') fica preso no default do TipTap. */
export function alinhamentoDoNo(valor: unknown): AlinhamentoMinuta {
  if (valor === 'left' || valor === 'center' || valor === 'right' || valor === 'justify') {
    return valor
  }
  return 'justify'
}

export function posicaoPainelGrifo(
  selecao: { top: number; bottom: number; left: number },
  viewport: { width: number; height: number },
  painel: { width: number; height: number } = {
    width: GRIFO_PAINEL_LARGURA,
    height: GRIFO_PAINEL_ALTURA,
  },
): { top: number | null; bottom: number | null; left: number; acima: boolean } {
  const largura = Math.min(painel.width, viewport.width - 32)
  const espacoAbaixo = viewport.height - selecao.bottom
  const acima = espacoAbaixo < painel.height + 16
  const left = Math.min(Math.max(16, selecao.left), viewport.width - largura - 16)
  if (acima) {
    return {
      top: null,
      bottom: viewport.height - selecao.top + GRIFO_PAINEL_FOLGA,
      left,
      acima: true,
    }
  }
  return {
    top: selecao.bottom + GRIFO_PAINEL_FOLGA,
    bottom: null,
    left,
    acima: false,
  }
}

const EXTENSOES_MODELO = ['txt', 'pdf', 'docx'] as const
export const MODELO_MAX_BYTES = 5 * 1024 * 1024

export function extensaoArquivo(nome: string): string {
  const pedaco = nome.split('.').pop()
  return pedaco ? pedaco.toLowerCase() : ''
}

/** null = ok. Mensagem = rejeitado. Não envia arquivo a servidor. */
export function validarArquivoModelo(arquivo: { name: string; size: number }): string | null {
  const ext = extensaoArquivo(arquivo.name)
  if (!(EXTENSOES_MODELO as readonly string[]).includes(ext)) {
    return 'Use um arquivo TXT, PDF ou DOCX.'
  }
  if (arquivo.size > MODELO_MAX_BYTES) {
    return 'O arquivo passa de 5 MB.'
  }
  return null
}
