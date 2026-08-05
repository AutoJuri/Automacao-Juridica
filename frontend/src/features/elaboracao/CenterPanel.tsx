import { DocumentToolbar } from './DocumentToolbar'
import { DocumentViewer } from './DocumentViewer'
import { EditorChatBar } from './EditorChatBar'
import { modelosPeca } from './elaboracao.mock'

interface CenterPanelProps {
  editando: boolean
  onToggleEditar: () => void
  highlightAtivo: boolean
  chatInput: string
  onChatChange: (v: string) => void
  pecaSelecionada: string
}

export function CenterPanel({
  editando,
  onToggleEditar,
  highlightAtivo,
  chatInput,
  onChatChange,
  pecaSelecionada,
}: CenterPanelProps) {
  const peca = modelosPeca.find((m) => m.id === pecaSelecionada)
  const pecaNome = peca?.nome ?? 'Contestação'

  return (
    <div className="flex flex-col flex-1 min-w-0 overflow-hidden bg-[#F0F2F7]">
      {/* Toolbar */}
      <div className="px-4 py-2.5 border-b border-[#E5E7EB] bg-white shrink-0">
        <DocumentToolbar editando={editando} onToggleEditar={onToggleEditar} />
      </div>

      {/* Document area */}
      <div className="flex-1 min-h-0 px-4 overflow-hidden flex flex-col">
        <DocumentViewer
          editando={editando}
          highlightAtivo={highlightAtivo}
          pecaNome={pecaNome}
        />
      </div>

      {/* Chat bar */}
      <EditorChatBar chatInput={chatInput} onChange={onChatChange} />
    </div>
  )
}
