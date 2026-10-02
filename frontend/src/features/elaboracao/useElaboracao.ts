import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import {
  atualizarFatosExtras,
  buscarSugestaoPeca,
  definirEstiloPorTexto,
  editarMinuta,
  gerarPrimeiraVersao,
  listarVersoes,
  obterOuCriarElaboracao,
  type EditarMinutaInput,
} from './elaboracao.api'
import {
  elaboracaoSessaoQueryKey,
  elaboracaoVersoesQueryKey,
  sugestaoPecaQueryKey,
} from './elaboracao.constants'
import type { VersaoMinutaApi } from './elaboracao.types'

/**
 * Sugestão de peça (ADR-016 Fase 1). Só a tela de elaboração chama isto —
 * o cabeçalho do processo não, para não gastar um pedido ao modelo a cada
 * ficha aberta. `staleTime` alto porque o palpite não muda a cada render.
 */
export function useSugestaoPeca(processoId: string | null, enabled = true) {
  return useQuery({
    queryKey: sugestaoPecaQueryKey(processoId),
    queryFn: () => buscarSugestaoPeca(processoId!),
    enabled: enabled && Boolean(processoId),
    staleTime: 5 * 60_000,
    // A sugestão dispara sozinha ao abrir a ficha. Um 500/429 não pode
    // virar outra chamada ao modelo. A cota fica para Elaborar, chat e grifo.
    retry: false,
  })
}

/**
 * Sessão de elaboração (fatos extras) + histórico de versões da minuta —
 * gerar/chat/grifo (ADR-016). `enabled` desliga tudo quando ainda não há
 * `processoId`/`peca` (ex.: ficha do processo ainda carregando).
 */
export function useElaboracao(processoId: string, peca: string, enabled = true) {
  const queryClient = useQueryClient()
  const podeCarregar = enabled && Boolean(processoId) && Boolean(peca)

  const sessaoQuery = useQuery({
    queryKey: elaboracaoSessaoQueryKey(processoId, peca),
    queryFn: () => obterOuCriarElaboracao(processoId, peca),
    enabled: podeCarregar,
    staleTime: 60_000,
  })

  const elaboracaoId = sessaoQuery.data?.id ?? null

  const versoesQuery = useQuery({
    queryKey: elaboracaoVersoesQueryKey(elaboracaoId),
    queryFn: () => listarVersoes(elaboracaoId!),
    enabled: Boolean(elaboracaoId),
  })

  function adicionarVersaoAoCache(versao: VersaoMinutaApi) {
    queryClient.setQueryData<VersaoMinutaApi[]>(
      elaboracaoVersoesQueryKey(elaboracaoId),
      (atuais) => [versao, ...(atuais ?? [])],
    )
  }

  const salvarFatosExtras = useMutation({
    mutationFn: (fatosExtras: string | null) => {
      if (!elaboracaoId) {
        throw new Error('Sessão de elaboração ainda não carregou.')
      }
      return atualizarFatosExtras(elaboracaoId, fatosExtras)
    },
    onSuccess: (sessao) => {
      queryClient.setQueryData(elaboracaoSessaoQueryKey(processoId, peca), sessao)
    },
  })

  const gerarMinuta = useMutation({
    mutationFn: () => {
      if (!elaboracaoId) {
        throw new Error('Sessão de elaboração ainda não carregou.')
      }
      return gerarPrimeiraVersao(elaboracaoId)
    },
    onSuccess: adicionarVersaoAoCache,
  })

  const editarMinutaMutation = useMutation({
    mutationFn: (body: EditarMinutaInput) => {
      if (!elaboracaoId) {
        throw new Error('Sessão de elaboração ainda não carregou.')
      }
      return editarMinuta(elaboracaoId, body)
    },
    onSuccess: adicionarVersaoAoCache,
  })

  const definirEstilo = useMutation({
    mutationFn: (texto: string) => {
      if (!elaboracaoId) {
        throw new Error('Sessão de elaboração ainda não carregou.')
      }
      return definirEstiloPorTexto(elaboracaoId, texto)
    },
    onSuccess: (sessao) => {
      queryClient.setQueryData(elaboracaoSessaoQueryKey(processoId, peca), sessao)
    },
  })

  return {
    elaboracaoId,
    sessaoQuery,
    versoesQuery,
    salvarFatosExtras,
    gerarMinuta,
    editarMinuta: editarMinutaMutation,
    definirEstilo,
  }
}
