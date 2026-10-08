/**
 * Só devolve o caminho de convite se ele for exatamente `/convite/{uuid}`.
 * Qualquer outro redirect é descartado — evita abrir o navegador em outro site.
 */

const CAMINHO_CONVITE =
  /^\/convite\/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/

export function destinoConvite(valor: string | undefined): string | null {
  if (!valor || !CAMINHO_CONVITE.test(valor)) {
    return null
  }
  return valor
}

export function tokenDoDestino(destino: string): string {
  return destino.slice('/convite/'.length)
}
