import { api } from '#/lib/axios'

import type { Coluna, Quadro, Tarefa } from './tarefas.types'

export interface ColunaApi {
  id: string
  title: string
  position: number
  is_done: boolean
  task_count: number
}

export interface TarefaApi {
  id: string
  column_id: string
  position: number
  title: string
  description: string
  assignee: { member_id: string | null; name: string } | null
  created_by: { name: string }
  processo: { id: string; nu_processo: string | null } | null
  due_date: string | null
  is_overdue: boolean
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface QuadroApi {
  title: string
  description: string
  columns: ColunaApi[]
  tasks: TarefaApi[]
}

export interface PaginaTarefasApi {
  tasks: TarefaApi[]
  total: number
}

export interface CorpoTarefa {
  title: string
  description: string
  column_id: string
  due_date: string | null
  processo_id: string | null
  assigned_to_member_id?: string
}

function quadroPath(orgId: string | null): string {
  return orgId ? `/organizations/${orgId}/tasks/board` : '/tasks/board'
}

function tarefasPath(orgId: string | null): string {
  return orgId ? `/organizations/${orgId}/tasks` : '/tasks'
}

function colunasPath(orgId: string | null): string {
  return orgId ? `/organizations/${orgId}/kanban/columns` : '/tasks/columns'
}

export async function atualizarQuadro(
  orgId: string | null,
  corpo: { title: string; description: string },
): Promise<QuadroApi> {
  const { data } = await api.patch<QuadroApi>(quadroPath(orgId), corpo)
  return data
}

export async function buscarQuadro(orgId: string | null): Promise<QuadroApi> {
  const { data } = await api.get<QuadroApi>(quadroPath(orgId))
  return data
}

export async function buscarPaginaConclusao(
  orgId: string | null,
  colunaId: string,
  offset: number,
): Promise<PaginaTarefasApi> {
  const { data } = await api.get<PaginaTarefasApi>(`${colunasPath(orgId)}/${colunaId}/tasks`, {
    params: { offset },
  })
  return data
}

export async function criarTarefa(orgId: string | null, corpo: CorpoTarefa): Promise<TarefaApi> {
  const json = orgId ? corpo : semResponsavel(corpo)
  const { data } = await api.post<TarefaApi>(tarefasPath(orgId), json)
  return data
}

export async function atualizarTarefa(
  orgId: string | null,
  tarefaId: string,
  corpo: Partial<CorpoTarefa>,
): Promise<TarefaApi> {
  const json = orgId ? corpo : semResponsavel(corpo)
  const { data } = await api.patch<TarefaApi>(`${tarefasPath(orgId)}/${tarefaId}`, json)
  return data
}

export async function moverTarefaApi(
  orgId: string | null,
  tarefaId: string,
  columnId: string,
  position: number,
): Promise<TarefaApi> {
  const { data } = await api.post<TarefaApi>(`${tarefasPath(orgId)}/${tarefaId}/move`, {
    column_id: columnId,
    position,
  })
  return data
}

export async function excluirTarefa(orgId: string | null, tarefaId: string): Promise<void> {
  await api.delete(`${tarefasPath(orgId)}/${tarefaId}`)
}

export async function criarColuna(orgId: string | null, title: string): Promise<ColunaApi> {
  const { data } = await api.post<ColunaApi>(colunasPath(orgId), { title })
  return data
}

export async function atualizarColuna(
  orgId: string | null,
  colunaId: string,
  corpo: { title?: string; is_done?: boolean },
): Promise<ColunaApi> {
  const { data } = await api.patch<ColunaApi>(`${colunasPath(orgId)}/${colunaId}`, corpo)
  return data
}

export async function removerColunaApi(orgId: string | null, colunaId: string): Promise<void> {
  await api.delete(`${colunasPath(orgId)}/${colunaId}`)
}

export function quadroDeApi(quadro: QuadroApi, pessoal: boolean, usuarioId: string): Quadro {
  const colunas = [...quadro.columns].sort((a, b) => a.position - b.position)
  const ordem = new Map(colunas.map((coluna, indice) => [coluna.id, indice]))
  const tarefas = [...quadro.tasks].sort((a, b) => {
    const colunaA = ordem.get(a.column_id) ?? 0
    const colunaB = ordem.get(b.column_id) ?? 0
    if (colunaA !== colunaB) {
      return colunaA - colunaB
    }
    return a.position - b.position
  })
  return {
    titulo: quadro.title,
    descricao: quadro.description,
    colunas: colunas.map(colunaDeApi),
    tarefas: tarefas.map((tarefa) => tarefaDeApi(tarefa, pessoal, usuarioId)),
  }
}

function colunaDeApi(coluna: ColunaApi): Coluna {
  return {
    id: coluna.id,
    titulo: coluna.title,
    conclusao: coluna.is_done,
    total: coluna.task_count,
  }
}

export function tarefasDaPagina(tarefas: TarefaApi[], pessoal: boolean, usuarioId: string): Tarefa[] {
  return [...tarefas]
    .sort((a, b) => a.position - b.position)
    .map((tarefa) => tarefaDeApi(tarefa, pessoal, usuarioId))
}

function tarefaDeApi(tarefa: TarefaApi, pessoal: boolean, usuarioId: string): Tarefa {
  return {
    id: tarefa.id,
    titulo: tarefa.title,
    descricao: tarefa.description,
    responsavelId: pessoal ? usuarioId : (tarefa.assignee?.member_id ?? ''),
    responsavelNome: tarefa.assignee?.name,
    processoId: tarefa.processo?.id ?? null,
    processoNumero: tarefa.processo?.nu_processo ?? null,
    prazo: tarefa.due_date,
    colunaId: tarefa.column_id,
    concluida: tarefa.completed_at !== null,
    criadorNome: tarefa.created_by.name,
  }
}

function semResponsavel(corpo: Partial<CorpoTarefa>): Partial<CorpoTarefa> {
  const { assigned_to_member_id: _ignorado, ...resto } = corpo
  return resto
}
