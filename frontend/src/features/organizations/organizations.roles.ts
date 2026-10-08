export type PapelOrg = 'owner' | 'admin' | 'advogado' | 'assistente' | 'estagiario'
export type PapelConvidavel = Exclude<PapelOrg, 'owner'>

export const ROTULO_PAPEL: Record<PapelOrg, string> = {
  owner: 'Owner',
  admin: 'Admin',
  advogado: 'Advogado',
  assistente: 'Assistente',
  estagiario: 'Estagiário',
}

export const PAPEIS_CONVIDAVEIS: PapelConvidavel[] = ['admin', 'advogado', 'assistente', 'estagiario']

export function podeGerenciar(role: string | undefined): boolean {
  return role === 'owner' || role === 'admin'
}

export function ehOwner(role: string | undefined): boolean {
  return role === 'owner'
}

export function rotuloPapel(role: string): string {
  if (role in ROTULO_PAPEL) {
    return ROTULO_PAPEL[role as PapelOrg]
  }
  return role
}
