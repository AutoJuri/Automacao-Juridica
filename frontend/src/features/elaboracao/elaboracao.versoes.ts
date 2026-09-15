const PREFIXO = 'advogativa.minuta.versoes'
const MAX_VERSOES = 20

export interface VersaoMinuta {
  id: string
  rotulo: string
  criadoEm: string
  html: string
}

export function chaveVersoes(processoId: string, pecaId: string): string {
  return `${PREFIXO}.${processoId}.${pecaId}`
}

export function lerVersoes(bruto: string | null): VersaoMinuta[] {
  if (!bruto) {
    return []
  }
  try {
    const parsed = JSON.parse(bruto) as unknown
    if (!Array.isArray(parsed)) {
      return []
    }
    return parsed.filter(isVersaoMinuta)
  } catch {
    return []
  }
}

export function adicionarVersao(
  atuais: VersaoMinuta[],
  html: string,
  agora: Date,
): VersaoMinuta[] {
  const nova: VersaoMinuta = {
    id: crypto.randomUUID(),
    rotulo: `Versão ${atuais.length + 1}`,
    criadoEm: agora.toISOString(),
    html,
  }
  return [nova, ...atuais].slice(0, MAX_VERSOES)
}

function isVersaoMinuta(item: unknown): item is VersaoMinuta {
  if (!item || typeof item !== 'object') {
    return false
  }
  const v = item as VersaoMinuta
  return (
    typeof v.id === 'string' &&
    typeof v.rotulo === 'string' &&
    typeof v.criadoEm === 'string' &&
    typeof v.html === 'string'
  )
}
