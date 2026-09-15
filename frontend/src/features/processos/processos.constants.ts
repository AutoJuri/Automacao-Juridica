export const PROCESSOS_QUERY_KEY = ['processos'] as const
export const INTIMACOES_QUERY_KEY = ['intimacoes'] as const
export const AUDIENCIAS_QUERY_KEY = ['audiencias'] as const

export function processoDetalheQueryKey(id: string) {
  return ['processos', id] as const
}
