import { api } from '#/lib/axios'
import type { ElaboracaoSessao, SugestaoPeca, VersaoMinutaApi } from './elaboracao.types'

export async function obterOuCriarElaboracao(
  processoId: string,
  peca: string,
): Promise<ElaboracaoSessao> {
  const { data } = await api.post<ElaboracaoSessao>('/elaboracoes', {
    processo_id: processoId,
    peca,
  })
  return data
}

export async function atualizarFatosExtras(
  elaboracaoId: string,
  fatosExtras: string | null,
): Promise<ElaboracaoSessao> {
  const { data } = await api.patch<ElaboracaoSessao>(`/elaboracoes/${elaboracaoId}`, {
    fatos_extras: fatosExtras,
  })
  return data
}

export async function gerarPrimeiraVersao(elaboracaoId: string): Promise<VersaoMinutaApi> {
  const { data } = await api.post<VersaoMinutaApi>(`/elaboracoes/${elaboracaoId}/gerar`)
  return data
}

export interface EditarMinutaInput {
  instrucao: string
  trechoSelecionado?: string | null
}

export async function editarMinuta(
  elaboracaoId: string,
  { instrucao, trechoSelecionado }: EditarMinutaInput,
): Promise<VersaoMinutaApi> {
  const { data } = await api.post<VersaoMinutaApi>(`/elaboracoes/${elaboracaoId}/editar`, {
    instrucao,
    trecho_selecionado: trechoSelecionado ?? null,
  })
  return data
}

export async function listarVersoes(elaboracaoId: string): Promise<VersaoMinutaApi[]> {
  const { data } = await api.get<VersaoMinutaApi[]>(`/elaboracoes/${elaboracaoId}/versoes`)
  return data
}

/** Sugestão determinística (modo stub) de peça a partir da intimação/movimento
 * mais recente do processo — o seletor continua livre (ADR-016 Fase 1). */
export async function buscarSugestaoPeca(processoId: string): Promise<SugestaoPeca> {
  const { data } = await api.get<SugestaoPeca>('/elaboracoes/sugestao-peca', {
    params: { processo_id: processoId },
  })
  return data
}

/** Envia o texto de um modelo (TXT lido no browser ou colado) para a IA
 * extrair um perfil de estilo desta sessão (ADR-016 Fase 3). */
export async function definirEstiloPorTexto(
  elaboracaoId: string,
  texto: string,
): Promise<ElaboracaoSessao> {
  const { data } = await api.post<ElaboracaoSessao>(`/elaboracoes/${elaboracaoId}/estilo`, {
    texto,
  })
  return data
}
