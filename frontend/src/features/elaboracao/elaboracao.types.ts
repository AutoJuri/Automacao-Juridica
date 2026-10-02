/** Tipos do payload da IA da elaboração (ADR-016) — nunca inclui campo `*_encrypted`. */

export interface ElaboracaoSessao {
  id: string
  processo_id: string
  peca: string
  fatos_extras: string | null
  // JSON (string) do perfil de estilo extraído do último modelo aplicado
  // nesta sessão (Fase 3) — `null` até o advogado aplicar um modelo.
  estilo_perfil: string | null
  created_at: string
  updated_at: string
}

/** `peca=null` = sem sugestão suficiente; o seletor continua no padrão (Fase 1). */
export interface SugestaoPeca {
  peca: string | null
  explicacao: string | null
}

export type OrigemVersaoMinuta = 'geracao' | 'chat' | 'grifo'

export interface VersaoMinutaApi {
  id: string
  origem: OrigemVersaoMinuta
  instrucao: string | null
  trecho_selecionado: string | null
  conteudo_html: string
  llm_provider: string
  llm_model: string | null
  criado_em: string
}
