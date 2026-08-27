import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { Navbar, NAVBAR_HEIGHT } from './Navbar'
import { ProcessoSidebar } from './ProcessoSidebar'
import { ProcessoDetalhe } from './ProcessoDetalhe'
import { ArbitroPesquisa } from './ArbitroPesquisa'
import { listarProcessos } from './processos.api'
import { PROCESSOS_QUERY_KEY } from './processos.constants'
import { type PortalKey } from './portais.mock'

function filtrarPorPortal<T extends { tribunal: string }>(itens: T[], portal: PortalKey): T[] {
  if (portal === 'todos') {
    return itens
  }
  return itens.filter((item) => item.tribunal === portal)
}

interface DashboardPageProps {
  /** UUID vindo do sino (`?processo=`) quando a notificação foi clicada fora da home. */
  processoInicial?: string
}

export function DashboardPage({ processoInicial }: DashboardPageProps) {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchDebounced, setSearchDebounced] = useState('')
  const [portalSelecionado, setPortalSelecionado] = useState<PortalKey>('todos')
  const [processoSelecionadoId, setProcessoSelecionadoId] = useState<string | null>(null)

  useEffect(() => {
    const handle = window.setTimeout(() => setSearchDebounced(searchQuery), 300)
    return () => window.clearTimeout(handle)
  }, [searchQuery])

  const listaQuery = useQuery({
    queryKey: [...PROCESSOS_QUERY_KEY, searchDebounced],
    queryFn: () => listarProcessos(searchDebounced),
  })

  const processosFiltrados = useMemo(
    () => filtrarPorPortal(listaQuery.data ?? [], portalSelecionado),
    [listaQuery.data, portalSelecionado],
  )

  useEffect(() => {
    if (!processoInicial) {
      return
    }
    setSearchQuery('')
    setPortalSelecionado('todos')
  }, [processoInicial])

  useEffect(() => {
    if (!processoInicial || listaQuery.isLoading || searchDebounced !== '') {
      return
    }
    const naLista = (listaQuery.data ?? []).some((p) => p.id === processoInicial)
    if (naLista) {
      setProcessoSelecionadoId(processoInicial)
    }
    void navigate({ to: '/', search: {}, replace: true })
  }, [processoInicial, listaQuery.isLoading, listaQuery.data, searchDebounced, navigate])

  useEffect(() => {
    if (processoInicial) {
      return
    }
    const selecionadoVisivel = processosFiltrados.some((p) => p.id === processoSelecionadoId)
    if (!selecionadoVisivel) {
      setProcessoSelecionadoId(processosFiltrados[0]?.id ?? null)
    }
  }, [processosFiltrados, processoSelecionadoId, processoInicial])

  return (
    <div className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden">
      <Navbar onAbrirProcesso={setProcessoSelecionadoId} />

      <div
        className="flex flex-1 overflow-hidden px-5 sm:px-8 lg:px-10 xl:px-14 py-5 gap-5 min-h-0"
        style={{ marginTop: NAVBAR_HEIGHT }}
      >
        <ProcessoSidebar
          processos={processosFiltrados}
          processoSelecionadoId={processoSelecionadoId}
          onSelect={setProcessoSelecionadoId}
          carregando={listaQuery.isLoading}
        />

        <div className="flex flex-1 flex-col gap-4 overflow-hidden min-w-0">
          <ArbitroPesquisa
            searchQuery={searchQuery}
            onSearchQueryChange={setSearchQuery}
            portalSelecionado={portalSelecionado}
            onPortalChange={setPortalSelecionado}
          />
          {listaQuery.isError ? (
            <div className="flex-1 flex items-center justify-center rounded-xl border border-[#E5E7EB] bg-white">
              <p className="text-sm text-[#9CA3AF] px-6 text-center">
                {mensagemDeErro(listaQuery.error, {
                  401: 'Sessão expirada. Entre novamente.',
                })}
              </p>
            </div>
          ) : (
            <ProcessoDetalhe processoId={processoSelecionadoId} />
          )}
        </div>
      </div>
    </div>
  )
}
