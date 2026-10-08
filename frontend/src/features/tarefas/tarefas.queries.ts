import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { listarMembros } from '#/features/organizations/organizations.api'
import { orgMembersKey } from '#/features/organizations/organizations.constants'
import { listarProcessos } from '#/features/processos/processos.api'
import { PROCESSOS_QUERY_KEY } from '#/features/processos/processos.constants'

import {
  atualizarColuna,
  atualizarQuadro,
  atualizarTarefa,
  buscarPaginaConclusao,
  buscarQuadro,
  criarColuna,
  criarTarefa,
  excluirTarefa,
  moverTarefaApi,
  quadroDeApi,
  removerColunaApi,
  tarefasDaPagina,
  type CorpoTarefa,
} from './tarefas.api'
import { incluirPagina } from './tarefas.board'
import { tarefasBoardKey } from './tarefas.constants'
import type { Quadro } from './tarefas.types'

export { TAREFAS_QUERY_KEY, tarefasBoardKey } from './tarefas.constants'

export function useMembrosParaTarefas(orgId: string | null) {
  return useQuery({
    queryKey: orgId ? orgMembersKey(orgId) : ['organizations', 'sem-contexto', 'members'],
    queryFn: () => listarMembros(orgId as string),
    enabled: orgId !== null,
  })
}

export function useProcessosParaTarefas() {
  return useQuery({
    queryKey: PROCESSOS_QUERY_KEY,
    queryFn: () => listarProcessos(),
  })
}

export function useQuadroTarefas(orgId: string | null, usuarioId: string | undefined) {
  return useQuery({
    queryKey: tarefasBoardKey(orgId),
    queryFn: async () => quadroDeApi(await buscarQuadro(orgId), orgId === null, usuarioId ?? ''),
    enabled: Boolean(usuarioId),
    staleTime: 60_000,
  })
}

export function useCriarTarefa(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (corpo: CorpoTarefa) => criarTarefa(orgId, corpo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}

export function useAtualizarTarefa(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { tarefaId: string; corpo: Partial<CorpoTarefa> }) =>
      atualizarTarefa(orgId, input.tarefaId, input.corpo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}

export function useExcluirTarefa(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (tarefaId: string) => excluirTarefa(orgId, tarefaId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}

export function useMoverTarefa(orgId: string | null) {
  const queryClient = useQueryClient()
  const chave = tarefasBoardKey(orgId)
  return useMutation({
    mutationFn: (input: { tarefaId: string; colunaId: string; posicao: number; proximo: Quadro }) =>
      moverTarefaApi(orgId, input.tarefaId, input.colunaId, input.posicao),
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: chave })
      const anterior = queryClient.getQueryData<Quadro>(chave)
      queryClient.setQueryData(chave, input.proximo)
      return { anterior }
    },
    onError: (_erro, _input, contexto) => {
      if (contexto?.anterior) {
        queryClient.setQueryData(chave, contexto.anterior)
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: chave })
    },
  })
}

export function useAtualizarQuadro(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (corpo: { title: string; description: string }) => atualizarQuadro(orgId, corpo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}

export function useCriarColuna(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (titulo: string) => criarColuna(orgId, titulo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}

export function useAtualizarColuna(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { colunaId: string; title?: string; is_done?: boolean }) =>
      atualizarColuna(orgId, input.colunaId, {
        ...(input.title !== undefined ? { title: input.title } : {}),
        ...(input.is_done !== undefined ? { is_done: input.is_done } : {}),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}

export function useCarregarMaisConcluidas(orgId: string | null, pessoal: boolean, usuarioId: string) {
  const queryClient = useQueryClient()
  const chave = tarefasBoardKey(orgId)
  return useMutation({
    mutationFn: async (input: { colunaId: string; offset: number }) => {
      const pagina = await buscarPaginaConclusao(orgId, input.colunaId, input.offset)
      return {
        colunaId: input.colunaId,
        total: pagina.total,
        tarefas: tarefasDaPagina(pagina.tasks, pessoal, usuarioId),
      }
    },
    onSuccess: (pagina) => {
      queryClient.setQueryData<Quadro>(chave, (quadro) =>
        quadro ? incluirPagina(quadro, pagina.colunaId, pagina.tarefas, pagina.total) : quadro,
      )
    },
  })
}

export function useRemoverColuna(orgId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (colunaId: string) => removerColunaApi(orgId, colunaId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: tarefasBoardKey(orgId) })
    },
  })
}
