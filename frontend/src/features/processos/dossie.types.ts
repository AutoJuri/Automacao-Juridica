export type StatusDossie =
  | 'ocioso'
  | 'lendo'
  | 'pronto'
  | 'bloqueado'
  | 'sessao_expirada'
  | 'limite_ia'
  | 'erro'
  | 'sem_documentos'

export type StatusDocumento =
  | 'pendente'
  | 'lido'
  | 'parcial'
  | 'sem_acesso'
  | 'ilegivel'
  | 'erro'

export interface DocumentoDossie {
  movimentacao_id: string
  titulo: string | null
  data: string | null
  status: string
}

export interface RoteiroAutos {
  resumo: string
  tese: string
  pedidos: string
  acrescentar: string
  nao_incluir: string
  jurisprudencia: string
}

export interface DossieAutos {
  processo_id: string
  status: string
  lidos: number
  total: number
  gerado_em: string | null
  retomar_apos: string | null
  resumo: string | null
  roteiro: RoteiroAutos
  documentos: DocumentoDossie[]
}
