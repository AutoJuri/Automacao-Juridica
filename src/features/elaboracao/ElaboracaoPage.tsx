import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Scale } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { Navbar, NAVBAR_HEIGHT } from '#/features/processos/Navbar'
import { LeftPanel } from './LeftPanel'
import { CenterPanel } from './CenterPanel'
import { RightPanel } from './RightPanel'
import { modelosPeca } from './elaboracao.mock'
import { processosMockados } from '#/features/processos/processos.mock'

interface ElaboracaoPageProps {
  processoId: number
}

export function ElaboracaoPage({ processoId }: ElaboracaoPageProps) {
  const navigate = useNavigate()
  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)
  const [pecaSelecionada, setPecaSelecionada] = useState(modelosPeca[0].id)
  const [editando, setEditando] = useState(false)
  const [highlightAtivo, setHighlightAtivo] = useState(false)
  const [chatInput, setChatInput] = useState('')

  const processo = processosMockados.find((p) => p.id === processoId)
  const pecaNome = modelosPeca.find((m) => m.id === pecaSelecionada)?.nome ?? 'Contestação'

  return (
    <div className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden">
      <Navbar />

      {/* Barra de contexto */}
      <div
        className="fixed left-0 right-0 z-40 flex items-center gap-3 px-6 bg-white border-b border-[#E5E7EB] shadow-sm"
        style={{ top: NAVBAR_HEIGHT, height: 44 }}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate({ to: '/' })}
          className="h-7 px-2 text-[11px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Voltar
        </Button>

        <div className="w-px h-4 bg-[#E5E7EB]" />

        <div className="flex items-center gap-2">
          <Scale className="w-3.5 h-3.5 text-[#9CA3AF]" />
          <span className="text-[11px] text-[#9CA3AF]">
            {processo?.numero ?? `Processo #${processoId}`}
          </span>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-[#9CA3AF]">
          <span>/</span>
          <span className="font-semibold text-[#374151]">{pecaNome}</span>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-1.5 text-[10px] text-[#9CA3AF]">
          <div className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
          Rascunho salvo
        </div>
      </div>

      {/* Layout 3 colunas */}
      <div
        className="flex flex-1 overflow-hidden min-h-0"
        style={{ marginTop: NAVBAR_HEIGHT + 44 }}
      >
        <LeftPanel
          collapsed={leftCollapsed}
          onToggle={() => setLeftCollapsed((v) => !v)}
          processoId={processoId}
          pecaSelecionada={pecaSelecionada}
          onPecaChange={setPecaSelecionada}
        />

        <CenterPanel
          editando={editando}
          onToggleEditar={() => setEditando((v) => !v)}
          highlightAtivo={highlightAtivo}
          chatInput={chatInput}
          onChatChange={setChatInput}
          pecaSelecionada={pecaSelecionada}
        />

        <RightPanel
          collapsed={rightCollapsed}
          onToggle={() => setRightCollapsed((v) => !v)}
          highlightAtivo={highlightAtivo}
          onToggleHighlight={setHighlightAtivo}
        />
      </div>
    </div>
  )
}
