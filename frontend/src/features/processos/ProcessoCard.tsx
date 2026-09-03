import type { ProcessoLista } from './processos.types'
import { formatarDataSP } from './processos.dates'
import { formatarNumeroCnj, rotuloTribunal } from './processos.format'
import { getPortalDoProcesso } from './portais.mock'

interface ProcessoCardProps {
  processo: ProcessoLista
  selecionado: boolean
  onClick: () => void
}

export function ProcessoCard({ processo, selecionado, onClick }: ProcessoCardProps) {
  const portal = getPortalDoProcesso(
    processo.tribunal === 'pje_trf3' ? 'pje_trf3' : 'esaj_tjsp',
  )
  const cliente = processo.parte_ativa?.nome?.trim() || 'Não informado'
  const numero = formatarNumeroCnj(processo.nu_processo)
  const atividade = processo.ultima_atividade

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'w-full text-left rounded-xl p-4 border bg-white transition-all duration-150 cursor-pointer',
        selecionado
          ? 'border-[#2563EB] shadow-sm ring-1 ring-[#2563EB]/15 border-l-[4px]'
          : 'border-[#E5E7EB] hover:border-[#C7D0E8] hover:bg-[#F8F9FC] hover:shadow-sm',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-1.5 min-w-0">
          <span
            className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide text-white"
            style={{ backgroundColor: portal.cor }}
          >
            {portal.tag}
          </span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold tracking-wide text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
            {rotuloTribunal(processo.tribunal)}
          </span>
        </div>
        <p className="text-[10px] font-medium text-[#6B7280] tabular-nums flex-shrink-0 pt-0.5">
          {atividade?.data ? formatarDataSP(atividade.data) : '—'}
        </p>
      </div>

      <p className="font-mono text-[13px] font-bold text-[#111827] tracking-tight leading-snug mb-1">
        {numero}
      </p>

      <p className="text-[12px] text-[#374151] font-medium mb-3">{cliente}</p>

      <div className="h-px bg-[#F3F4F6] mb-3" />

      <p className="text-[9px] font-semibold text-[#9CA3AF] uppercase tracking-[0.14em] mb-1">
        Última Alteração:
      </p>
      <p className="text-[11px] text-[#6B7280] leading-relaxed line-clamp-3">
        {atividade?.titulo?.trim() || 'Ainda sem evento coletado'}
      </p>
    </button>
  )
}
