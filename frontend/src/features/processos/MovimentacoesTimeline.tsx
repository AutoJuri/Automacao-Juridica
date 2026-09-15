import { FileText } from 'lucide-react'
import type { MovimentacaoPublica, MovimentacoesStatus } from './processos.types'
import { formatarDataSP } from './processos.dates'

interface MovimentacoesTimelineProps {
  movimentacoes: MovimentacaoPublica[]
  selecionadoId: string | null
  onSelect: (id: string) => void
  status?: MovimentacoesStatus
}

const MENSAGEM_VAZIA: Record<MovimentacoesStatus, string> = {
  ok: 'Nenhuma movimentação coletada para este processo.',
  pendente:
    'As movimentações deste processo ainda não foram buscadas no e-SAJ. Elas entram no próximo ciclo de coleta.',
  indisponivel:
    'Sem acesso às movimentações deste processo no e-SAJ (segredo de justiça ou sem vínculo pleno). Não solicitamos senha dos autos.',
}

export function MovimentacoesTimeline({
  movimentacoes,
  selecionadoId,
  onSelect,
  status = 'pendente',
}: MovimentacoesTimelineProps) {
  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="shrink-0 px-5 pt-5 pb-3">
        <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
          Movimentações ({movimentacoes.length})
        </p>
        <p className="text-[11px] text-[#9CA3AF] mt-1">Clique para inspecionar</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 min-h-0">
        {movimentacoes.length === 0 ? (
          <p className="text-[12px] text-[#9CA3AF] leading-relaxed px-1">
            {MENSAGEM_VAZIA[status]}
          </p>
        ) : (
          <div className="space-y-2.5">
            {movimentacoes.map((item) => {
              const isSelected = item.id === selecionadoId
              const detalhe = item.descricao.trim()
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelect(item.id)}
                  className={[
                    'w-full text-left rounded-xl px-4 py-3.5 border transition-all duration-150 cursor-pointer',
                    isSelected
                      ? 'border-[#2563EB] bg-white shadow-sm ring-1 ring-[#2563EB]/15'
                      : 'border-[#E5E7EB] bg-white hover:border-[#C7D0E8] hover:bg-[#F8F9FC]',
                  ].join(' ')}
                >
                  <div className="flex items-center justify-between gap-3 mb-1.5">
                    <span className="text-[11px] font-medium text-[#6B7280] tabular-nums">
                      {formatarDataSP(item.data_movimentacao)}
                    </span>
                    {item.tem_documento ? (
                      <span
                        className="inline-flex items-center text-[#6B7280]"
                        title="Há documento no e-SAJ"
                        aria-label="Há documento no e-SAJ"
                      >
                        <FileText className="w-3.5 h-3.5" aria-hidden />
                      </span>
                    ) : null}
                  </div>
                  <p className="text-[13px] font-semibold text-[#111827] leading-snug">
                    {item.titulo?.trim() || 'Movimentação'}
                  </p>
                  {detalhe ? (
                    <p className="text-[12px] text-[#6B7280] leading-relaxed mt-1 line-clamp-2">
                      {detalhe}
                    </p>
                  ) : null}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
