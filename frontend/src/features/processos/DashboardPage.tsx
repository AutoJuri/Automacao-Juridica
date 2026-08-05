import { useEffect, useMemo, useState } from 'react'
import { Navbar, NAVBAR_HEIGHT } from './Navbar'
import { ProcessoSidebar } from './ProcessoSidebar'
import { ProcessoDetalhe } from './ProcessoDetalhe'
import { ArbitroPesquisa } from './ArbitroPesquisa'
import { processosMockados } from './processos.mock'
import { filtrarProcessos, type PortalKey } from './portais.mock'

export function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [portalSelecionado, setPortalSelecionado] = useState<PortalKey>('todos')
  const [processoSelecionadoId, setProcessoSelecionadoId] = useState<number>(
    processosMockados[0]?.id ?? 1,
  )

  const processosFiltrados = useMemo(
    () => filtrarProcessos(processosMockados, portalSelecionado, searchQuery),
    [portalSelecionado, searchQuery],
  )

  useEffect(() => {
    const selecionadoVisivel = processosFiltrados.some((p) => p.id === processoSelecionadoId)
    if (!selecionadoVisivel) {
      setProcessoSelecionadoId(processosFiltrados[0]?.id ?? 0)
    }
  }, [processosFiltrados, processoSelecionadoId])

  return (
    <div className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden">
      <Navbar />

      <div
        className="flex flex-1 overflow-hidden px-5 sm:px-8 lg:px-10 xl:px-14 py-5 gap-5 min-h-0"
        style={{ marginTop: NAVBAR_HEIGHT }}
      >
        <ProcessoSidebar
          processos={processosFiltrados}
          processoSelecionadoId={processoSelecionadoId}
          onSelect={setProcessoSelecionadoId}
        />

        <div className="flex flex-1 flex-col gap-4 overflow-hidden min-w-0">
          <ArbitroPesquisa
            searchQuery={searchQuery}
            onSearchQueryChange={setSearchQuery}
            portalSelecionado={portalSelecionado}
            onPortalChange={setPortalSelecionado}
          />
          <ProcessoDetalhe processoId={processoSelecionadoId} />
        </div>
      </div>
    </div>
  )
}
