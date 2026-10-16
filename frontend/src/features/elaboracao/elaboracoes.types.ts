export interface ElaboracaoCard {
  id: string
  peca: string
  rotulo: string
  titulo: string | null
  nu_processo: string | null
  autor: string | null
  reu: string | null
  tem_processo: boolean
  updated_at: string
}

export interface ElaboracaoManual {
  titulo: string
  nu_processo: string | null
  parte_ativa: string | null
  parte_passiva: string | null
  classe: string | null
  assunto: string | null
  foro_vara: string | null
  valor_causa: string | null
  juiz: string | null
}

export interface ElaboracaoDetalhe extends ElaboracaoCard {
  processo_id: string | null
  manual: ElaboracaoManual | null
}

export interface UltimaAtividadeProcesso {
  tipo: 'intimacao' | 'audiencia'
  titulo: string | null
  data: string | null
}

export interface ProcessoParaIniciar {
  id: string
  nu_processo: string | null
  tribunal: string
  classe: string | null
  autor: string | null
  reu: string | null
  ultima_atividade: UltimaAtividadeProcesso | null
}

export interface PaginaProcessosParaIniciar {
  items: ProcessoParaIniciar[]
  total: number
}

export interface RascunhoManual {
  peca: string
  titulo: string
  nu_processo: string
  parte_ativa: string
  parte_passiva: string
  classe: string
  assunto: string
  foro_vara: string
  valor_causa: string
  juiz: string
}
