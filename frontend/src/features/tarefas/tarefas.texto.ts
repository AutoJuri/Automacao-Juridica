export function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) {
    return '?'
  }
  if (partes.length === 1) {
    return partes[0].slice(0, 2).toUpperCase()
  }
  return `${partes[0][0]}${partes[partes.length - 1][0]}`.toUpperCase()
}

export function formatarPrazo(prazo: string): string {
  const [ano, mes, dia] = prazo.split('-')
  if (!ano || !mes || !dia) {
    return prazo
  }
  return `${dia}/${mes}/${ano}`
}

export function trecho(texto: string, max = 120): string {
  const limpo = texto.replace(/\s+/g, ' ').trim()
  if (limpo.length <= max) {
    return limpo
  }
  return `${limpo.slice(0, max - 1).trimEnd()}…`
}
