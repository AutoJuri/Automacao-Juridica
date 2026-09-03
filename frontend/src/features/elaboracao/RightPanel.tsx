import { PanelRightClose, PanelRightOpen } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { ScrollArea } from '#/components/ui/scroll-area'
import { Separator } from '#/components/ui/separator'
import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { MedidorCompletude } from './MedidorCompletude'
import { JurisprudenciaPanel } from './JurisprudenciaPanel'
import { HistoricoVersoes } from './HistoricoVersoes'
import type { VersaoMinuta } from './elaboracao.versoes'

interface RightPanelProps {
  collapsed: boolean
  onToggle: () => void
  processo: ProcessoDetalhe | null
  versoes: VersaoMinuta[]
  versaoAtivaId: string | null
  onSalvarVersao: () => void
  onRestaurarVersao: (id: string) => void
}

export function RightPanel({
  collapsed,
  onToggle,
  processo,
  versoes,
  versaoAtivaId,
  onSalvarVersao,
  onRestaurarVersao,
}: RightPanelProps) {
  return (
    <aside
      className="flex flex-col bg-white border-l border-[#E5E7EB] transition-all duration-300 overflow-hidden shrink-0"
      style={{ width: collapsed ? 44 : 352 }}
    >
      <div
        className={`flex items-center py-3 px-2.5 border-b border-[#E5E7EB] shrink-0 ${collapsed ? 'justify-center' : 'justify-between'}`}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="h-7 w-7 p-0 text-[#6B7280] hover:text-[#374151] hover:bg-[#F3F4F6]"
          title={collapsed ? 'Expandir painel direito' : 'Recolher painel direito'}
        >
          {collapsed ? (
            <PanelRightOpen className="w-4 h-4" />
          ) : (
            <PanelRightClose className="w-4 h-4" />
          )}
        </Button>
        {!collapsed ? (
          <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.16em] uppercase px-1">
            Análise & jurisprudência
          </p>
        ) : null}
      </div>

      {!collapsed && (
        <ScrollArea className="flex-1 min-h-0">
          <div className="p-4 space-y-5">
            <MedidorCompletude processo={processo} />
            <Separator className="bg-[#E5E7EB]" />
            <JurisprudenciaPanel />
            <Separator className="bg-[#E5E7EB]" />
            <HistoricoVersoes
              versoes={versoes}
              versaoAtivaId={versaoAtivaId}
              onSalvar={onSalvarVersao}
              onRestaurar={onRestaurarVersao}
            />
          </div>
        </ScrollArea>
      )}

      {collapsed ? (
        <div className="flex-1 flex flex-col items-center pt-4">
          <span
            className="text-[9px] font-semibold text-[#9CA3AF] tracking-widest uppercase"
            style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
          >
            Análise
          </span>
        </div>
      ) : null}
    </aside>
  )
}
