/**
 * Contratos do painel de processos, espelhando `backend/app/schemas/processo.py`.
 * `id_esaj` nunca aparece — o id público é o UUID nosso.
 */

export interface PartePublica {
  nome: string | null
  representada: boolean | null
}

export type TipoAtividade = 'intimacao' | 'audiencia'

export interface UltimaAtividade {
  tipo: TipoAtividade
  titulo: string | null
  data: string | null
}

export interface ProcessoLista {
  id: string
  tribunal: string
  nu_processo: string | null
  de_classe: string | null
  de_assunto: string | null
  instancia: string | null
  parte_ativa: PartePublica | null
  parte_passiva: PartePublica | null
  last_synced_at: string | null
  ultima_atividade: UltimaAtividade | null
  fixado: boolean
}

export interface IntimacaoPublica {
  id: string
  titulo: string | null
  descricao: string | null
  instancia: string | null
  data_movimentacao: string | null
  ciencia: boolean
}

export interface AudienciaPublica {
  id: string
  titulo: string | null
  data_audiencia: string | null
  local: string | null
}

export interface MovimentacaoPublica {
  id: string
  titulo: string | null
  descricao: string
  data_movimentacao: string | null
  tem_documento: boolean
  /** Só https do e-SAJ para o documento vinculado; senha dos autos nunca vira URL. */
  url_documento: string | null
}

export type MovimentacoesStatus = 'ok' | 'pendente' | 'indisponivel'

export interface ParteCpoPublica {
  papel: string
  nome: string | null
  advogados: string | null
}

export interface PeticaoDiversaPublica {
  id: string
  data_peticao: string | null
  tipo: string
  protocolo: string | null
}

export interface AudienciaCpoPublica {
  id: string
  data_audiencia: string | null
  titulo: string
  situacao: string | null
  qt_pessoas: string | null
}

export interface DatajudAssuntoPublica {
  codigo: number | null
  nome: string | null
}

export interface DatajudMovimentoPublica {
  codigo: number | null
  nome: string | null
  data_hora: string | null
}

/**
 * Complemento somente-leitura do DataJud (CNJ) — Etapa 9. Nunca sobrescreve
 * os campos que vêm do e-SAJ (`de_classe`, `de_assunto`, `foro`, `vara`...),
 * é sempre uma seção separada. `null` = ainda não passou pelo job diário.
 */
export interface ProcessoDatajudPublica {
  classe_nome: string | null
  assuntos: DatajudAssuntoPublica[]
  orgao_julgador: string | null
  data_ajuizamento: string | null
  grau: string | null
  formato: string | null
  movimentos: DatajudMovimentoPublica[]
  encontrado: boolean
  ultima_consulta_em: string | null
}

export interface ProcessoDetalhe extends ProcessoLista {
  url_cpo: string | null
  url_pasta: string | null
  foro: string | null
  vara: string | null
  juiz: string | null
  distribuicao: string | null
  controle: string | null
  area: string | null
  valor_acao: string | null
  partes_cpo: ParteCpoPublica[]
  intimacoes: IntimacaoPublica[]
  audiencias: AudienciaPublica[]
  movimentacoes: MovimentacaoPublica[]
  peticoes_diversas: PeticaoDiversaPublica[]
  audiencias_cpo: AudienciaCpoPublica[]
  movimentacoes_status: MovimentacoesStatus
  sem_incidentes: boolean | null
  sem_apensos: boolean | null
  datajud: ProcessoDatajudPublica | null
}

export interface IntimacaoPainel {
  id: string
  processo_id: string | null
  nu_processo: string | null
  tribunal: string | null
  instancia: string | null
  titulo: string | null
  descricao: string | null
  data_movimentacao: string | null
  ciencia: boolean
  foro: string | null
  vara: string | null
}

export interface AudienciaPainel {
  id: string
  processo_id: string | null
  nu_processo: string | null
  tribunal: string | null
  titulo: string
  data_audiencia: string | null
  local: string | null
  situacao: string | null
  parte_ativa: PartePublica | null
  parte_passiva: PartePublica | null
  foro: string | null
  vara: string | null
  juiz: string | null
  /** Assunto do processo (`de_assunto`) — objeto do requerimento. */
  de_assunto: string | null
  fonte: 'agenda' | 'cpo'
}
