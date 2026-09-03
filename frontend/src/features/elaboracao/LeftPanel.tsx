import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { ScrollArea } from '#/components/ui/scroll-area'
import { Separator } from '#/components/ui/separator'
import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { SeletorPeca } from './SeletorPeca'
import { InformacoesProcessoPanel } from './InformacoesProcessoPanel'
import { SeletorPecaEspecifica } from './SeletorPecaEspecifica'

interface LeftPanelProps {
  collapsed: boolean
  onToggle: () => void
  pecaSelecionada: string
  onPecaChange: (id: string) => void
  processo: ProcessoDetalhe | null
  carregando: boolean
}

export function LeftPanel({
  collapsed,
  onToggle,
  pecaSelecionada,
  onPecaChange,
  processo,
  carregando,
}: LeftPanelProps) {
  return (
    <aside
      className="flex flex-col bg-white border-r border-[#E5E7EB] transition-all duration-300 overflow-hidden shrink-0"
      style={{ width: collapsed ? 44 : 352 }}
    >
      <div
        className={`flex items-center py-3 px-2.5 border-b border-[#E5E7EB] shrink-0 ${collapsed ? 'justify-center' : 'justify-between'}`}
      >
        {!collapsed ? (
          <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.16em] uppercase px-1">
            Dados & modelo
          </p>
        ) : null}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="h-7 w-7 p-0 text-[#6B7280] hover:text-[#374151] hover:bg-[#F3F4F6]"
          title={collapsed ? 'Expandir painel esquerdo' : 'Recolher painel esquerdo'}
        >
          {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </Button>
      </div>

      {!collapsed && (
        <ScrollArea className="flex-1 min-h-0">
          <div className="p-4 space-y-5">
            <SeletorPeca pecaSelecionada={pecaSelecionada} onChange={onPecaChange} />
            <Separator className="bg-[#E5E7EB]" />
            <InformacoesProcessoPanel processo={processo} carregando={carregando} />
            <Separator className="bg-[#E5E7EB]" />
            <SeletorPecaEspecifica />
          </div>
        </ScrollArea>
      )}

      {collapsed ? (
        <div className="flex-1 flex flex-col items-center pt-4">
          <span
            className="text-[9px] font-semibold text-[#9CA3AF] tracking-widest uppercase"
            style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
          >
            Dados
          </span>
        </div>
      ) : null}
    </aside>
  )
}
