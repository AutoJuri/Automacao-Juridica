/** Cargo do perfil da conta. Não é o papel dentro de uma organização. */

export const CARGOS = ['advogado', 'assistente', 'estagiario'] as const

export type CargoPerfil = (typeof CARGOS)[number]

export const ROTULO_CARGO: Record<CargoPerfil, string> = {
  advogado: 'Advogado',
  assistente: 'Assistente',
  estagiario: 'Estagiário',
}

export function rotuloCargo(cargo: string | null | undefined): string {
  if (cargo && cargo in ROTULO_CARGO) {
    return ROTULO_CARGO[cargo as CargoPerfil]
  }
  return 'Não informado'
}
