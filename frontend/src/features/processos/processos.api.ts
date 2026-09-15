import { api } from '#/lib/axios'
import type {
  AudienciaPainel,
  IntimacaoPainel,
  ProcessoDetalhe,
  ProcessoLista,
} from './processos.types'

export async function listarProcessos(q?: string): Promise<ProcessoLista[]> {
  const { data } = await api.get<ProcessoLista[]>('/processos', {
    params: q?.trim() ? { q: q.trim() } : undefined,
  })
  return data
}

export async function buscarProcesso(id: string): Promise<ProcessoDetalhe> {
  const { data } = await api.get<ProcessoDetalhe>(`/processos/${id}`)
  return data
}

export async function atualizarFixado(
  id: string,
  fixado: boolean,
): Promise<{ id: string; fixado: boolean }> {
  const { data } = await api.patch<{ id: string; fixado: boolean }>(`/processos/${id}`, {
    fixado,
  })
  return data
}

export async function listarIntimacoes(): Promise<IntimacaoPainel[]> {
  const { data } = await api.get<IntimacaoPainel[]>('/intimacoes')
  return data
}

export async function listarAudiencias(): Promise<AudienciaPainel[]> {
  const { data } = await api.get<AudienciaPainel[]>('/audiencias')
  return data
}
