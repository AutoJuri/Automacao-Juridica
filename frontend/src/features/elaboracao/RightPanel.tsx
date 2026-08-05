import { PanelRightClose, PanelRightOpen } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { ScrollArea } from '#/components/ui/scroll-area'
import { Separator } from '#/components/ui/separator'
import { MedidorCompletude } from './MedidorCompletude'
import { JurisprudenciaPanel } from './JurisprudenciaPanel'
import { HistoricoVersoes } from './HistoricoVersoes'
import { ViewOptionsPanel } from './ViewOptionsPanel'

interface RightPanelProps {
  collapsed: boolean
  onToggle: () => void
  highlightAtivo: boolean
  onToggleHighlight: (v: boolean) => void
}

export function RightPanel({
  collapsed,
  onToggle,
  highlightAtivo,
  onToggleHighlight,
}: RightPanelProps) {
  return (
    <aside
      className="flex flex-col bg-elaboracao-sidebar border-l border-border-active transition-all duration-300 overflow-hidden shrink-0"
      style={{ width: collapsed ? 44 : 300 }}
    >
      {/* Toggle button */}
      <div className={`flex items-center py-3 px-2.5 border-b border-border-active bg-elaboracao-sidebar-muted shrink-0 ${collapsed ? 'justify-center' : 'justify-start'}`}>
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="h-7 w-7 p-0 text-[#6B7280] hover:text-[#374151] hover:bg-elaboracao-sidebar-hover"
          title={collapsed ? 'Expandir painel direito' : 'Recolher painel direito'}
        >
          {collapsed ? (
            <PanelRightOpen className="w-4 h-4" />
          ) : (
            <PanelRightClose className="w-4 h-4" />
          )}
        </Button>
      </div>

      {!collapsed && (
        <ScrollArea className="flex-1 min-h-0">
          <div className="p-4 space-y-5">
            <MedidorCompletude />

            <Separator className="bg-border-active" />

            <JurisprudenciaPanel />

            <Separator className="bg-border-active" />

            <HistoricoVersoes />

            <Separator className="bg-border-active" />

            <ViewOptionsPanel
              highlightAtivo={highlightAtivo}
              onToggleHighlight={onToggleHighlight}
            />
          </div>
        </ScrollArea>
      )}

      {collapsed && (
        <div className="flex-1 flex flex-col items-center pt-4 gap-3">
          <div className="w-5 h-16 flex items-center justify-center">
            <span
              className="text-[9px] font-semibold text-[#9CA3AF] tracking-widest uppercase"
              style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
            >
              Info
            </span>
          </div>
        </div>
      )}
    </aside>
  )
}
