import { api } from '#/lib/axios'
import type { ProcessoDetalhe, ProcessoLista } from './processos.types'

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
