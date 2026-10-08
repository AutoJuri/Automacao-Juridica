export const TAREFAS_QUERY_KEY = ['tarefas'] as const

export function tarefasBoardKey(orgId: string | null) {
  return ['tarefas', 'board', orgId ?? 'pessoal'] as const
}
