import { useEffect, useMemo, useState } from 'react'
import type { Editor } from '@tiptap/react'
import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { DocumentFormatToolbar } from './DocumentToolbar'
import { DocumentViewer } from './DocumentViewer'
import { EditorChatBar } from './EditorChatBar'
import { GrifoSelecaoPanel } from './GrifoSelecaoPanel'
import { posicaoPainelGrifo } from './elaboracao.ui'
import { montarHtmlMinuta } from './elaboracao.minuta'
import { modelosPeca } from './elaboracao.mock'
import { useMinutaEditor } from './useMinutaEditor'

interface CenterPanelProps {
  editando: boolean
  highlightAtivo: boolean
  iconesJuris: boolean
  onToggleHighlight: (v: boolean) => void
  onToggleIcones: (v: boolean) => void
  chatInput: string
  onChatChange: (v: string) => void
  pecaSelecionada: string
  processo: ProcessoDetalhe | null
  carregando: boolean
  onEditorChange: (editor: Editor | null) => void
}

export function CenterPanel({
  editando,
  highlightAtivo,
  iconesJuris,
  onToggleHighlight,
  onToggleIcones,
  chatInput,
  onChatChange,
  pecaSelecionada,
  processo,
  carregando,
  onEditorChange,
}: CenterPanelProps) {
  const pecaNome = modelosPeca.find((m) => m.id === pecaSelecionada)?.nome ?? 'Contestação'
  const html = useMemo(
    () => (processo ? montarHtmlMinuta(processo, pecaNome) : ''),
    [processo, pecaNome],
  )
  const chave = `${processo?.id ?? ''}:${pecaNome}`
  const editor = useMinutaEditor({ html, chave, editando })
  const [, setTick] = useState(0)
  const [fonte, setFonte] = useState('Times New Roman, Times, serif')
  const [tamanho, setTamanho] = useState('12pt')
  const [espacamento, setEspacamento] = useState('1.5')
  const [grifo, setGrifo] = useState<{
    trecho: string
    top: number | null
    bottom: number | null
    left: number
  } | null>(null)

  useEffect(() => {
    onEditorChange(editor)
    return () => onEditorChange(null)
  }, [editor, onEditorChange])

  useEffect(() => {
    if (!editor) {
      return
    }
    const bump = () => setTick((n) => n + 1)
    editor.on('transaction', bump)
    editor.on('selectionUpdate', bump)
    return () => {
      editor.off('transaction', bump)
      editor.off('selectionUpdate', bump)
    }
  }, [editor])

  useEffect(() => {
    if (!editor) {
      return
    }
    const atualizar = () => {
      if (!highlightAtivo) {
        setGrifo(null)
        return
      }
      const { from, to, empty } = editor.state.selection
      if (empty) {
        setGrifo(null)
        return
      }
      const trecho = editor.state.doc.textBetween(from, to, ' ')
      const inicio = editor.view.coordsAtPos(from)
      const fimPos = Math.max(from, Math.min(to, editor.state.doc.content.size) - 1)
      const fim = editor.view.coordsAtPos(fimPos)
      const pos = posicaoPainelGrifo(
        { top: inicio.top, bottom: fim.bottom, left: inicio.left },
        { width: window.innerWidth, height: window.innerHeight },
      )
      setGrifo({ trecho, top: pos.top, bottom: pos.bottom, left: pos.left })
    }
    editor.on('selectionUpdate', atualizar)
    return () => {
      editor.off('selectionUpdate', atualizar)
    }
  }, [editor, highlightAtivo])

  useEffect(() => {
    if (!highlightAtivo) {
      setGrifo(null)
    }
  }, [highlightAtivo])

  return (
    <div className="flex flex-col flex-1 min-w-0 overflow-hidden bg-[#F0F2F7]">
      <DocumentFormatToolbar
        editor={editor}
        editando={editando}
        fonte={fonte}
        tamanho={tamanho}
        espacamento={espacamento}
        onFonte={setFonte}
        onTamanho={setTamanho}
        onEspacamento={setEspacamento}
      />

      <div className="flex-1 min-h-0 px-4 overflow-hidden flex flex-col">
        <DocumentViewer
          editor={editor}
          editando={editando}
          carregando={carregando}
          fonte={fonte}
          tamanho={tamanho}
          espacamento={espacamento}
        />
      </div>

      {grifo ? (
        <GrifoSelecaoPanel
          trecho={grifo.trecho}
          top={grifo.top}
          bottom={grifo.bottom}
          left={grifo.left}
          onFechar={() => setGrifo(null)}
        />
      ) : null}

      <EditorChatBar
        chatInput={chatInput}
        onChange={onChatChange}
        highlightAtivo={highlightAtivo}
        iconesJuris={iconesJuris}
        onToggleHighlight={onToggleHighlight}
        onToggleIcones={onToggleIcones}
      />
    </div>
  )
}
