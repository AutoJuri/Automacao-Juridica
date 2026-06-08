import { processosMockados } from './processos.mock'
import { ProcessoCard } from './ProcessoCard'

interface ProcessoSidebarProps {
  processoSelecionadoId: number
  onSelect: (id: number) => void
}

export function ProcessoSidebar({ processoSelecionadoId, onSelect }: ProcessoSidebarProps) {
  return (
    <aside className="flex flex-col w-[340px] min-w-[340px] max-w-[340px] h-full rounded-xl border border-[#E5E7EB] bg-[#F5F6FA] overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-[#E5E7EB]">
        <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.2em] uppercase mb-1.5">
          Módulo Lateral
        </p>
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-[15px] font-semibold text-[#111827] leading-snug">
            Processos em Acompanhamento
          </h2>
          <span className="inline-flex flex-shrink-0 items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-white border border-[#E5E7EB] text-[#6B7280]">
            {processosMockados.length} Ativos
          </span>
        </div>
      </div>

      {/* Cards list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {processosMockados.map((processo) => (
          <ProcessoCard
            key={processo.id}
            processo={processo}
            selecionado={processo.id === processoSelecionadoId}
            onClick={() => onSelect(processo.id)}
          />
        ))}
      </div>

      {/* Footer note */}
      <div className="px-5 py-4 border-t border-[#E5E7EB] bg-[#F5F6FA]">
        <p className="text-[10px] text-[#9CA3AF] leading-relaxed">
          * Para fixar ou desfixar qualquer processo da barra lateral de acompanhamento, use o botão
          &quot;Fixar Acompanhamento&quot; presente no painel central do respectivo auto processual
          pesquisado.
        </p>
      </div>
    </aside>
  )
}
