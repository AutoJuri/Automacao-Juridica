import { api } from '#/lib/axios'

import type {
  ElaboracaoCard,
  ElaboracaoDetalhe,
  PaginaProcessosParaIniciar,
  RascunhoManual,
} from './elaboracoes.types'

export async function listarElaboracoes(q?: string): Promise<ElaboracaoCard[]> {
  const { data } = await api.get<ElaboracaoCard[]>('/elaboracoes', {
    params: q?.trim() ? { q: q.trim() } : undefined,
  })
  return data
}

export async function listarProcessosParaIniciar(
  offset: number,
  q?: string,
): Promise<PaginaProcessosParaIniciar> {
  const { data } = await api.get<PaginaProcessosParaIniciar>('/elaboracoes/a-iniciar', {
    params: {
      offset,
      ...(q?.trim() ? { q: q.trim() } : {}),
    },
  })
  return data
}

export async function criarElaboracaoDeProcesso(
  processoId: string,
  peca: string,
): Promise<ElaboracaoDetalhe> {
  const { data } = await api.post<ElaboracaoDetalhe>('/elaboracoes', {
    peca,
    processo_id: processoId,
  })
  return data
}

export async function criarElaboracaoManual(rascunho: RascunhoManual): Promise<ElaboracaoDetalhe> {
  const { data } = await api.post<ElaboracaoDetalhe>('/elaboracoes', {
    peca: rascunho.peca,
    manual: {
      titulo: rascunho.titulo.trim(),
      nu_processo: limpar(rascunho.nu_processo),
      parte_ativa: limpar(rascunho.parte_ativa),
      parte_passiva: limpar(rascunho.parte_passiva),
      classe: limpar(rascunho.classe),
      assunto: limpar(rascunho.assunto),
      foro_vara: limpar(rascunho.foro_vara),
      valor_causa: limpar(rascunho.valor_causa),
      juiz: limpar(rascunho.juiz),
    },
  })
  return data
}

export async function buscarElaboracao(id: string): Promise<ElaboracaoDetalhe> {
  const { data } = await api.get<ElaboracaoDetalhe>(`/elaboracoes/${id}`)
  return data
}

export async function atualizarElaboracao(
  id: string,
  corpo: {
    peca?: string
    manual?: {
      titulo: string
      nu_processo?: string
      parte_ativa?: string
      parte_passiva?: string
      classe?: string
      assunto?: string
      foro_vara?: string
      valor_causa?: string
      juiz?: string
    }
  },
): Promise<ElaboracaoDetalhe> {
  const { data } = await api.patch<ElaboracaoDetalhe>(`/elaboracoes/${id}`, corpo)
  return data
}

export async function excluirElaboracao(id: string): Promise<void> {
  await api.delete(`/elaboracoes/${id}`)
}

function limpar(valor: string): string | undefined {
  const texto = valor.trim()
  return texto || undefined
}
