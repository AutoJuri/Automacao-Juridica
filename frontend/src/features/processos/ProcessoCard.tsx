import type { ProcessoLista } from './processos.types'
import { formatarDataSP } from './processos.dates'
import { getPortalDoProcesso } from './portais.mock'

interface ProcessoCardProps {
  processo: ProcessoLista
  selecionado: boolean
  onClick: () => void
}

const TRIBUNAL_ROTULO: Record<string, string> = {
  esaj_tjsp: 'TJSP',
}

function rotuloTribunal(tribunal: string): string {
  return TRIBUNAL_ROTULO[tribunal] ?? tribunal.toUpperCase()
}

export function ProcessoCard({ processo, selecionado, onClick }: ProcessoCardProps) {
  const portal = getPortalDoProcesso(
    processo.tribunal === 'pje_trf3' ? 'pje_trf3' : 'esaj_tjsp',
  )
  const cliente = processo.parte_ativa?.nome?.trim() || 'Não informado'
  const numero = processo.nu_processo?.trim() || 'Número não informado'
  const atividade = processo.ultima_atividade

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'w-full text-left rounded-xl p-4 border transition-all duration-150 cursor-pointer',
        selecionado
          ? 'border-[#C7D0E8] bg-white shadow-sm ring-1 ring-[#C7D0E8]/50'
          : 'border-[#E5E7EB] bg-white hover:bg-[#F8F9FC] hover:border-[#C7D0E8]',
      ].join(' ')}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
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
      </div>

      <p className="font-mono text-[13px] font-bold text-[#111827] tracking-tight leading-snug mb-1">
        {numero}
      </p>

      <p className="text-[12px] text-[#374151] font-medium mb-3">{cliente}</p>

      <div className="h-px bg-[#F3F4F6] mb-3" />

      <div className="flex items-baseline justify-between gap-2 mb-1.5">
        <p className="text-[9px] font-semibold text-[#9CA3AF] uppercase tracking-[0.14em]">
          Última Alteração:
        </p>
        <p className="text-[10px] font-medium text-[#6B7280] tabular-nums flex-shrink-0">
          {atividade?.data ? formatarDataSP(atividade.data) : '—'}
        </p>
      </div>
      <p className="text-[11px] text-[#6B7280] leading-relaxed line-clamp-3">
        {atividade?.titulo?.trim() || 'Ainda sem evento coletado'}
      </p>
    </button>
  )
}
