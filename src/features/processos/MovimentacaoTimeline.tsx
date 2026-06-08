import { useState } from 'react'
import type { Movimentacao } from './processos.mock'

interface MovimentacaoTimelineProps {
  movimentacoes: Movimentacao[]
}

export function MovimentacaoTimeline({ movimentacoes }: MovimentacaoTimelineProps) {
  const [selecionadoId, setSelecionadoId] = useState<number>(movimentacoes[0]?.id ?? 0)

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
          Etapas Judiciais ({movimentacoes.length}/5)
        </p>
        <p className="text-[11px] text-[#9CA3AF] mt-1">
          Selecione para carregar a documentação relacionada
        </p>
      </div>

      <div className="space-y-3">
        {movimentacoes.map((mov) => {
          const isSelected = mov.id === selecionadoId

          return (
            <button
              key={mov.id}
              type="button"
              onClick={() => setSelecionadoId(mov.id)}
              className={[
                'w-full text-left rounded-xl px-4 py-3.5 border transition-all duration-150',
                isSelected
                  ? 'border-[#8B5CF6] bg-[#FAF5FF] shadow-sm'
                  : 'border-[#E5E7EB] bg-white hover:border-[#C7D0E8] hover:bg-[#F8F9FC]',
              ].join(' ')}
            >
              <div className="flex items-center justify-between gap-3 mb-2">
                <span className="text-[11px] font-medium text-[#6B7280]">{mov.data}</span>
                <span
                  className={[
                    'text-[9px] font-bold tracking-wider px-2 py-0.5 rounded-md border',
                    isSelected
                      ? 'border-[#8B5CF6] bg-[#8B5CF6] text-white'
                      : 'border-[#E5E7EB] bg-[#F3F4F6] text-[#6B7280]',
                  ].join(' ')}
                >
                  {mov.fase}
                </span>
              </div>
              <p className="text-[12px] text-[#374151] leading-relaxed">
                {mov.descricao}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
