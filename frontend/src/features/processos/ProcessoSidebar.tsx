import type { ProcessoLista } from './processos.types'
import { ProcessoCard } from './ProcessoCard'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'

interface ProcessoSidebarProps {
  processos: ProcessoLista[]
  processoSelecionadoId: string | null
  onSelect: (id: string) => void
  carregando?: boolean
}

export function ProcessoSidebar({
  processos,
  processoSelecionadoId,
  onSelect,
  carregando = false,
}: ProcessoSidebarProps) {
  return (
    <aside className="flex flex-col w-[340px] min-w-[340px] max-w-[340px] h-full rounded-2xl border border-[#E5E7EB] bg-white overflow-hidden shadow-sm">
      <div className="px-5 pt-5 pb-4 border-b border-[#E5E7EB]">
        <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.2em] uppercase mb-1.5">
          Módulo Lateral
        </p>
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-[15px] font-semibold text-[#111827] leading-snug">
            Processos em Acompanhamento
          </h2>
          <span className="inline-flex flex-shrink-0 items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#F3F4F6] border border-[#E5E7EB] text-[#6B7280]">
            {carregando ? '…' : `${processos.length} Ativos`}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 bg-[#F8F9FC] flex flex-col">
        {carregando ? (
          <EstadoCarregando mensagem="Carregando processos…" />
        ) : processos.length === 0 ? (
          <p className="text-center text-[12px] text-[#9CA3AF] py-8 px-2 leading-relaxed">
            Nenhum processo coletado ainda. O ciclo puxa processos que tiveram intimação ou
            audiência.
          </p>
        ) : (
          <div className="space-y-3">
            {processos.map((processo) => (
              <ProcessoCard
                key={processo.id}
                processo={processo}
                selecionado={processo.id === processoSelecionadoId}
                onClick={() => onSelect(processo.id)}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
