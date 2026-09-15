const ESAJ_HOST = 'esaj.tjsp.jus.br'
const PATH_DOCUMENTO = '/cpopg/abrirDocumentoVinculadoMovimentacao.do'

function parseHttps(url: string): URL | null {
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:') return null
    if (parsed.hostname !== ESAJ_HOST) return null
    if (parsed.username || parsed.password) return null
    return parsed
  } catch {
    return null
  }
}

/** Só `https://esaj.tjsp.jus.br/...` — defesa de XSS no `href` da SPA. */
export function urlEsajHttps(url: string | null | undefined): string | null {
  if (!url) return null
  const trimmed = url.trim()
  return parseHttps(trimmed) ? trimmed : null
}

/** URL direta do documento vinculado no CPO. Outros paths do e-SAJ não passam. */
export function urlDocumentoEsaj(url: string | null | undefined): string | null {
  if (!url) return null
  const trimmed = url.trim()
  const parsed = parseHttps(trimmed)
  if (!parsed || parsed.pathname !== PATH_DOCUMENTO) return null
  return trimmed
}

/**
 * Link que a timeline abre no browser do advogado.
 * Documento direto quando o CPO deu `abrirDocumentoVinculadoMovimentacao.do`;
 * senão a ficha CPO (`#liberarAutoPorSenha` pede senha dos autos — nunca vira URL nossa).
 */
export function hrefDocumentoMovimentacao(
  temDocumento: boolean,
  urlDocumento: string | null | undefined,
  urlCpo: string | null | undefined,
): string | null {
  if (!temDocumento) return null
  return urlDocumentoEsaj(urlDocumento) ?? urlEsajHttps(urlCpo)
}
