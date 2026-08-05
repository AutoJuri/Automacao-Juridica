import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { ScrollArea } from '#/components/ui/scroll-area'
import { SeletorPeca } from './SeletorPeca'
import { InformacoesProcessoPanel } from './InformacoesProcessoPanel'
import { SeletorPecaEspecifica } from './SeletorPecaEspecifica'
import { Separator } from '#/components/ui/separator'

interface LeftPanelProps {
  collapsed: boolean
  onToggle: () => void
  processoId: number
  pecaSelecionada: string
  onPecaChange: (id: string) => void
}

export function LeftPanel({
  collapsed,
  onToggle,
  processoId,
  pecaSelecionada,
  onPecaChange,
}: LeftPanelProps) {
  return (
    <aside
      className="flex flex-col bg-elaboracao-sidebar border-r border-border-active transition-all duration-300 overflow-hidden shrink-0"
      style={{ width: collapsed ? 44 : 288 }}
    >
      {/* Toggle button */}
      <div className={`flex items-center py-3 px-2.5 border-b border-border-active bg-elaboracao-sidebar-muted shrink-0 ${collapsed ? 'justify-center' : 'justify-end'}`}>
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="h-7 w-7 p-0 text-[#6B7280] hover:text-[#374151] hover:bg-elaboracao-sidebar-hover"
          title={collapsed ? 'Expandir painel esquerdo' : 'Recolher painel esquerdo'}
        >
          {collapsed ? (
            <PanelLeftOpen className="w-4 h-4" />
          ) : (
            <PanelLeftClose className="w-4 h-4" />
          )}
        </Button>
      </div>

      {!collapsed && (
        <ScrollArea className="flex-1 min-h-0">
          <div className="p-4 space-y-5">
            <SeletorPeca
              pecaSelecionada={pecaSelecionada}
              onChange={onPecaChange}
            />

            <Separator className="bg-border-active" />

            <InformacoesProcessoPanel processoId={processoId} />

            <Separator className="bg-border-active" />

            <SeletorPecaEspecifica />
          </div>
        </ScrollArea>
      )}

      {collapsed && (
        <div className="flex-1 flex flex-col items-center pt-4 gap-3">
          <div
            className="w-5 h-16 flex items-center justify-center"
            title="Seletor de Peça"
          >
            <span
              className="text-[9px] font-semibold text-[#9CA3AF] tracking-widest uppercase"
              style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
            >
              Peça
            </span>
          </div>
        </div>
      )}
    </aside>
  )
}
