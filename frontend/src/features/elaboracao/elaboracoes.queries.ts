import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  atualizarElaboracao,
  buscarElaboracao,
  criarElaboracaoDeProcesso,
  criarElaboracaoManual,
  excluirElaboracao,
  listarElaboracoes,
  listarProcessosParaIniciar,
} from './elaboracoes.api'
import {
  ELABORACOES_QUERY_KEY,
  elaboracaoDetalheKey,
  elaboracoesAIniciarKey,
  elaboracoesListaKey,
} from './elaboracoes.constants'
import type { ElaboracaoDetalhe, RascunhoManual } from './elaboracoes.types'

export function useElaboracoes(q: string) {
  return useQuery({
    queryKey: elaboracoesListaKey(q),
    queryFn: () => listarElaboracoes(q),
  })
}

export function useProcessosParaIniciar(q: string) {
  return useInfiniteQuery({
    queryKey: elaboracoesAIniciarKey(q),
    queryFn: ({ pageParam }) => listarProcessosParaIniciar(pageParam, q),
    initialPageParam: 0,
    getNextPageParam: (ultima, paginas) => {
      const carregados = paginas.reduce((total, pagina) => total + pagina.items.length, 0)
      return carregados < ultima.total ? carregados : undefined
    },
  })
}

export function useElaboracao(id: string) {
  return useQuery({
    queryKey: elaboracaoDetalheKey(id),
    queryFn: () => buscarElaboracao(id),
  })
}

export function useCriarElaboracao() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (
      entrada: { processoId: string; peca: string } | { manual: RascunhoManual },
    ) => {
      if ('manual' in entrada) {
        return criarElaboracaoManual(entrada.manual)
      }
      return criarElaboracaoDeProcesso(entrada.processoId, entrada.peca)
    },
    onSuccess: async () => {
      await cliente.invalidateQueries({ queryKey: ELABORACOES_QUERY_KEY })
    },
  })
}

export function useAtualizarElaboracao(id: string) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (corpo: Parameters<typeof atualizarElaboracao>[1]) =>
      atualizarElaboracao(id, corpo),
    onSuccess: async (detalhe) => {
      cliente.setQueryData<ElaboracaoDetalhe>(elaboracaoDetalheKey(id), (atual) => {
        if (atual && atual.updated_at > detalhe.updated_at) {
          return atual
        }
        return detalhe
      })
      await cliente.invalidateQueries({ queryKey: elaboracoesListaKey('') })
    },
  })
}

export function useExcluirElaboracao() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: excluirElaboracao,
    onSuccess: async () => {
      await cliente.invalidateQueries({ queryKey: ELABORACOES_QUERY_KEY })
    },
  })
}
