export interface Coluna {
  id: string
  titulo: string
  /** A coluna que marca a tarefa como concluída. No máximo uma por quadro. */
  conclusao: boolean
  /** Tarefas visíveis na coluna. Na de conclusão pode ser maior que as já carregadas. */
  total: number
}

export interface Tarefa {
  id: string
  titulo: string
  descricao: string
  /** No contexto pessoal é o id do usuário. Na organização é o id do membership. */
  responsavelId: string
  processoId: string | null
  /** Data `YYYY-MM-DD`, ou null. */
  prazo: string | null
  colunaId: string
  /** Nome vindo da API. A busca por id é só reserva. */
  responsavelNome?: string
  processoNumero?: string | null
  concluida?: boolean
  criadorNome?: string
}

export interface Quadro {
  titulo: string
  descricao: string
  colunas: Coluna[]
  tarefas: Tarefa[]
}

export interface RascunhoTarefa {
  titulo: string
  descricao: string
  responsavelId: string
  processoId: string | null
  prazo: string | null
}
