const CNJ_DIGITOS = 20

const INSTANCIA_GRAU: Record<string, string> = {
  PG: '1º Grau',
  SG: '2º Grau',
}

const TRIBUNAL_ROTULO: Record<string, string> = {
  esaj_tjsp: 'TJSP',
  pje_trf3: 'TRF3',
}

const PORTAL_ROTULO: Record<string, string> = {
  esaj_tjsp: 'e-SAJ',
  pje_trf3: 'PJe',
}

export function formatarNumeroCnj(valor: string | null | undefined): string {
  const bruto = valor?.trim()
  if (!bruto) {
    return 'Número não informado'
  }
  const digitos = bruto.replace(/\D/g, '')
  if (digitos.length !== CNJ_DIGITOS) {
    return bruto
  }
  return [
    digitos.slice(0, 7),
    '-',
    digitos.slice(7, 9),
    '.',
    digitos.slice(9, 13),
    '.',
    digitos.slice(13, 14),
    '.',
    digitos.slice(14, 16),
    '.',
    digitos.slice(16, 20),
  ].join('')
}

export function rotuloTribunal(tribunal: string): string {
  return TRIBUNAL_ROTULO[tribunal] ?? tribunal.toUpperCase()
}

export function rotuloPortal(tribunal: string): string {
  return PORTAL_ROTULO[tribunal] ?? tribunal.toUpperCase()
}

export function rotuloGrau(instancia: string | null | undefined): string | null {
  const chave = instancia?.trim().toUpperCase()
  if (!chave) {
    return null
  }
  return INSTANCIA_GRAU[chave] ?? instancia?.trim() ?? null
}

export function tagTribunalGrau(
  tribunal: string,
  instancia: string | null | undefined,
): string {
  const tribunalRotulo = rotuloTribunal(tribunal)
  const grau = rotuloGrau(instancia)
  return grau ? `${tribunalRotulo} · ${grau}` : tribunalRotulo
}

export function juntarLocalProcesso(
  foro: string,
  area: string,
  vara: string,
): string {
  return [foro, area, vara].filter(Boolean).join(' - ')
}

export async function copiarTexto(texto: string): Promise<boolean> {
  const conteudo = texto.trim()
  if (!conteudo) {
    return false
  }
  try {
    await navigator.clipboard.writeText(conteudo)
    return true
  } catch {
    return false
  }
}

export function escapeHtml(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function imprimirTexto(titulo: string, corpo: string): void {
  const janela = window.open('', '_blank', 'noopener,noreferrer')
  if (!janela) {
    return
  }
  const tituloSeguro = escapeHtml(titulo.trim() || 'Movimentação')
  const corpoSeguro = escapeHtml(corpo)
  janela.document.open()
  janela.document.write(
    `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>${tituloSeguro}</title></head><body><pre style="white-space:pre-wrap;font-family:Georgia,serif;font-size:14px;line-height:1.6">${corpoSeguro}</pre></body></html>`,
  )
  janela.document.close()
  janela.focus()
  janela.print()
}
