import { useState } from 'react'
import type { IntimacaoPublica } from './processos.types'
import { formatarDataHoraSP } from './processos.dates'

interface IntimacaoTimelineProps {
  intimacoes: IntimacaoPublica[]
}

export function IntimacaoTimeline({ intimacoes }: IntimacaoTimelineProps) {
  const [selecionadoId, setSelecionadoId] = useState<string | null>(intimacoes[0]?.id ?? null)

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
          Manifestações / ciência
        </p>
        <p className="text-[11px] text-[#9CA3AF] mt-1">
          Intimações coletadas do e-SAJ para este processo
        </p>
      </div>

      {intimacoes.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF] leading-relaxed">
          Nenhuma intimação coletada para este processo.
        </p>
      ) : (
        <div className="space-y-3">
          {intimacoes.map((item) => {
            const isSelected = item.id === selecionadoId
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelecionadoId(item.id)}
                className={[
                  'w-full text-left rounded-xl px-4 py-3.5 border transition-all duration-150',
                  isSelected
                    ? 'border-[#8B5CF6] bg-[#FAF5FF] shadow-sm'
                    : 'border-[#E5E7EB] bg-white hover:border-[#C7D0E8] hover:bg-[#F8F9FC]',
                ].join(' ')}
              >
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className="text-[11px] font-medium text-[#6B7280] tabular-nums">
                    {formatarDataHoraSP(item.data_movimentacao)}
                  </span>
                  <span
                    className={[
                      'text-[9px] font-bold tracking-wide px-2 py-0.5 rounded-md border',
                      item.ciencia
                        ? 'border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D]'
                        : 'border-[#FDE68A] bg-[#FFFBEB] text-[#B45309]',
                    ].join(' ')}
                  >
                    {item.ciencia ? 'Ciência dada' : 'Sem ciência'}
                  </span>
                </div>
                <p className="text-[12px] font-semibold text-[#111827] leading-snug mb-1">
                  {item.titulo?.trim() || 'Intimação'}
                </p>
                {item.descricao ? (
                  <p className="text-[12px] text-[#374151] leading-relaxed whitespace-pre-wrap">
                    {item.descricao}
                  </p>
                ) : null}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
