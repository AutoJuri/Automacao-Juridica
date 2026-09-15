import type { Processo, TribunalKey } from './processos.mock'

export type PortalKey = 'todos' | 'esaj_tjsp' | 'pje_trf3'
export type ProcessoPortalKey = Exclude<PortalKey, 'todos'>

export interface Portal {
  value: PortalKey
  label: string
  tribunal: TribunalKey | null
  tag: string
  cor: string
}

export const portaisDisponiveis: Portal[] = [
  { value: 'todos', label: 'Todos os Portais', tribunal: null, tag: 'Todos', cor: '#6B7280' },
  { value: 'esaj_tjsp', label: 'e-SAJ — TJSP', tribunal: 'TJSP', tag: 'e-SAJ', cor: '#3B5BDB' },
  { value: 'pje_trf3', label: 'PJe — TRF3', tribunal: 'TRF3', tag: 'PJe', cor: '#F97316' },
]

export function getPortalDoProcesso(portal: ProcessoPortalKey): Portal {
  const encontrado = portaisDisponiveis.find((p) => p.value === portal)
  if (!encontrado) {
    return portaisDisponiveis[1]
  }
  return encontrado
}

export function getPortalPorTribunal(tribunal: TribunalKey): Portal {
  const encontrado = portaisDisponiveis.find((p) => p.tribunal === tribunal)
  if (!encontrado) {
    return portaisDisponiveis[1]
  }
  return encontrado
}

export function filtrarProcessos(
  processos: Processo[],
  portal: PortalKey,
  searchQuery: string,
): Processo[] {
  const portalConfig = portaisDisponiveis.find((p) => p.value === portal)
  let resultado = processos

  if (portalConfig?.tribunal) {
    resultado = resultado.filter((p) => p.tribunal === portalConfig.tribunal)
  }

  const termo = searchQuery.trim().toLowerCase()
  if (termo) {
    resultado = resultado.filter(
      (p) =>
        p.numero.toLowerCase().includes(termo) ||
        p.cliente.toLowerCase().includes(termo) ||
        p.tribunal.toLowerCase().includes(termo) ||
        p.classeJudicial.toLowerCase().includes(termo),
    )
  }

  return resultado
}
