export const PROCESSOS_QUERY_KEY = ['processos'] as const

export function processoDetalheQueryKey(id: string) {
  return ['processos', id] as const
}
