import { api } from '#/lib/axios'
import type { DossieAutos, RoteiroAutos } from './dossie.types'

export function dossieQueryKey(processoId: string) {
  return ['processos', processoId, 'dossie'] as const
}

export async function buscarDossie(processoId: string): Promise<DossieAutos> {
  const { data } = await api.get<DossieAutos>(`/processos/${processoId}/dossie`)
  return data
}

export async function iniciarLeitura(processoId: string): Promise<DossieAutos> {
  const { data } = await api.post<DossieAutos>(`/processos/${processoId}/dossie/ler`)
  return data
}

export async function salvarRoteiro(processoId: string, roteiro: RoteiroAutos): Promise<DossieAutos> {
  const { data } = await api.put<DossieAutos>(`/processos/${processoId}/dossie/roteiro`, roteiro)
  return data
}
