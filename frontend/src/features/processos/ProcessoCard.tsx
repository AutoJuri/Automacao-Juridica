import type { Processo } from './processos.mock'
import { getPrazoUrgencia } from './prazo.utils'
import { getPortalDoProcesso } from './portais.mock'

interface ProcessoCardProps {
  processo: Processo
  selecionado: boolean
  onClick: () => void
}

export function ProcessoCard({ processo, selecionado, onClick }: ProcessoCardProps) {
  const { cor: prazoCor } = getPrazoUrgencia(processo.prazoInicio, processo.prazoFim)
  const portal = getPortalDoProcesso(processo.portal)

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
      {/* Top row — tag do portal + data do prazo */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <span
            className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide text-white"
            style={{ backgroundColor: portal.cor }}
          >
            {portal.tag}
          </span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold tracking-wide text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
            {processo.tribunal}
          </span>
        </div>
        <span
          className="inline-flex items-center gap-1.5 text-[11px] font-semibold tabular-nums"
          style={{ color: prazoCor }}
        >
          <span
            className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: prazoCor }}
          />
          {processo.prazoFim}
        </span>
      </div>

      {/* Process number */}
      <p className="font-mono text-[13px] font-bold text-[#111827] tracking-tight leading-snug mb-1">
        {processo.numero}
      </p>

      {/* Client name */}
      <p className="text-[12px] text-[#374151] font-medium mb-3">
        {processo.cliente}
      </p>

      {/* Divider */}
      <div className="h-px bg-[#F3F4F6] mb-3" />

      {/* Last update — label + date on same line */}
      <div className="flex items-baseline justify-between gap-2 mb-1.5">
        <p className="text-[9px] font-semibold text-[#9CA3AF] uppercase tracking-[0.14em]">
          Última Alteração:
        </p>
        <p className="text-[10px] font-medium text-[#6B7280] tabular-nums flex-shrink-0">
          {processo.dataUltimaAlteracao}
        </p>
      </div>
      <p className="text-[11px] text-[#6B7280] leading-relaxed line-clamp-3 mb-3">
        {processo.ultimaAlteracao}
      </p>

      {/* Próximo passo */}
      <div className="rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 py-2.5">
        <p className="text-[9px] font-semibold text-[#9CA3AF] uppercase tracking-[0.14em] mb-1">
          Próximo Passo
        </p>
        <p className="text-[11px] font-semibold text-[#111827] leading-snug uppercase">
          {processo.proximoPasso}
        </p>
      </div>
    </button>
  )
}
