export const ELABORACOES_QUERY_KEY = ['elaboracoes'] as const

export function elaboracoesListaKey(q: string) {
  return [...ELABORACOES_QUERY_KEY, 'lista', q] as const
}

export function elaboracoesAIniciarKey(q: string) {
  return [...ELABORACOES_QUERY_KEY, 'a-iniciar', q] as const
}

export function elaboracaoDetalheKey(id: string) {
  return [...ELABORACOES_QUERY_KEY, 'detalhe', id] as const
}
