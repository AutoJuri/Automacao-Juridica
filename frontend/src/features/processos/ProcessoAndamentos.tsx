import { useEffect, useState } from 'react'
import { DetalheMovimentacao } from './DetalheMovimentacao'
import { MovimentacoesTimeline } from './MovimentacoesTimeline'
import type { MovimentacaoPublica, MovimentacoesStatus } from './processos.types'

interface ProcessoAndamentosProps {
  processoId: string
  movimentacoes: MovimentacaoPublica[]
  status: MovimentacoesStatus
  urlCpo: string | null
  numeroProcesso: string | null
}

export function ProcessoAndamentos({
  processoId,
  movimentacoes,
  status,
  urlCpo,
  numeroProcesso,
}: ProcessoAndamentosProps) {
  const [selecionadoId, setSelecionadoId] = useState<string | null>(null)

  useEffect(() => {
    setSelecionadoId(null)
  }, [processoId])

  const selecionada =
    movimentacoes.find((item) => item.id === selecionadoId) ?? movimentacoes[0] ?? null

  return (
    <section
      // 3rem = py-5 do dashboard (2.5rem) + pb-2 do detalhe (0.5rem). A navbar entra por --navbar-height.
      className="shrink-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm overflow-hidden grid grid-cols-1 lg:grid-cols-2 lg:h-[calc(100vh-var(--navbar-height)-3rem)]"
    >
      <div className="min-h-[50vh] lg:min-h-0 lg:h-full border-b lg:border-b-0 lg:border-r border-[#E5E7EB]">
        <MovimentacoesTimeline
          movimentacoes={movimentacoes}
          selecionadoId={selecionada?.id ?? null}
          onSelect={setSelecionadoId}
          status={status}
        />
      </div>
      <div className="min-h-[50vh] lg:min-h-0 lg:h-full">
        <DetalheMovimentacao
          movimentacao={selecionada}
          urlCpo={urlCpo}
          numeroProcesso={numeroProcesso}
          total={movimentacoes.length}
        />
      </div>
    </section>
  )
}
