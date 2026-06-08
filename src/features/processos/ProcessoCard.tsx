import type { Processo } from './processos.mock'

interface ProcessoCardProps {
  processo: Processo
  selecionado: boolean
  onClick: () => void
}

export function ProcessoCard({ processo, selecionado, onClick }: ProcessoCardProps) {
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
      {/* Top row — tribunal badge + prazo badge */}
      <div className="flex items-center justify-between mb-3">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-semibold tracking-wide text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
          {processo.tribunal}
        </span>
        <span
          className="inline-flex items-center gap-1.5 text-[10px] font-semibold tracking-[0.08em] uppercase"
          style={{ color: processo.prazoColor }}
        >
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: processo.prazoColor }}
          />
          {processo.prazo}
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

      {/* Last update label */}
      <p className="text-[9px] font-semibold text-[#9CA3AF] uppercase tracking-[0.14em] mb-1.5">
        Última Alteração:
      </p>
      <p className="text-[11px] text-[#6B7280] leading-relaxed line-clamp-3">
        {processo.ultimaAlteracao}
      </p>
    </button>
  )
}
