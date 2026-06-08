import { useState } from 'react'
import { Navbar, NAVBAR_HEIGHT } from './Navbar'
import { ProcessoSidebar } from './ProcessoSidebar'
import { ProcessoDetalhe } from './ProcessoDetalhe'
import { processosMockados } from './processos.mock'

export function DashboardPage() {
  const [processoSelecionadoId, setProcessoSelecionadoId] = useState<number>(
    processosMockados[0]?.id ?? 1
  )

  return (
    <div className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden">
      <Navbar />

      {/* Conteúdo com padding lateral para centralizar */}
      <div
        className="flex flex-1 overflow-hidden px-5 sm:px-8 lg:px-10 xl:px-14 py-5 gap-5 min-h-0"
        style={{ marginTop: NAVBAR_HEIGHT }}
      >
        <ProcessoSidebar
          processoSelecionadoId={processoSelecionadoId}
          onSelect={setProcessoSelecionadoId}
        />
        <ProcessoDetalhe processoId={processoSelecionadoId} />
      </div>
    </div>
  )
}
