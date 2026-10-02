import { useEffect, useMemo, useState } from 'react'
import type { Editor } from '@tiptap/react'
import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { isAxiosError } from 'axios'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { DocumentFormatToolbar } from './DocumentToolbar'
import { DocumentViewer } from './DocumentViewer'
import { EditorChatBar } from './EditorChatBar'
import { GrifoSelecaoPanel } from './GrifoSelecaoPanel'
import { posicaoPainelGrifo } from './elaboracao.ui'
import { montarHtmlMinuta } from './elaboracao.minuta'
import { sanitizarHtmlMinuta } from './elaboracao.sanitize'
import { modelosPeca } from './elaboracao.mock'
import { useMinutaEditor } from './useMinutaEditor'
import type { useElaboracao } from './useElaboracao'

const ERROS_ELABORACAO: Record<number, string> = {
  404: 'Sessão de elaboração não encontrada. Recarregue a página.',
  409: 'Gere a primeira versão (Elaborar) antes de conversar ou grifar.',
  422: 'Instrução inválida — revise o texto.',
  429: 'Cota do modelo esgotada agora. Aguarde um pouco e clique de novo, sem recarregar a página.',
  503: 'O modelo de IA configurado não pode ser usado neste ambiente.',
}

function mensagemEditar(erro: unknown): string {
  if (isAxiosError(erro) && erro.response?.status === 409) {
    const detail = erro.response.data?.detail
    if (typeof detail === 'string' && detail.length > 0 && detail.length <= 200) {
      return detail
    }
  }
  return mensagemDeErro(erro, ERROS_ELABORACAO)
}

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
  elaboracao: ReturnType<typeof useElaboracao>
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
  elaboracao,
}: CenterPanelProps) {
  const pecaNome = modelosPeca.find((m) => m.id === pecaSelecionada)?.nome ?? 'Contestação'
  const versaoMaisRecente = elaboracao.versoesQuery.data?.[0] ?? null
  const html = useMemo(() => {
    if (versaoMaisRecente) {
      return sanitizarHtmlMinuta(versaoMaisRecente.conteudo_html)
    }
    return processo ? montarHtmlMinuta(processo, pecaNome) : ''
  }, [processo, pecaNome, versaoMaisRecente])
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

  const erroGerar = elaboracao.gerarMinuta.error
    ? mensagemDeErro(elaboracao.gerarMinuta.error, ERROS_ELABORACAO)
    : null
  const erroEditar = elaboracao.editarMinuta.error
    ? mensagemEditar(elaboracao.editarMinuta.error)
    : null

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
          executando={elaboracao.editarMinuta.isPending}
          erro={erroEditar}
          onExecutar={(instrucao) => {
            elaboracao.editarMinuta.mutate(
              { instrucao, trechoSelecionado: grifo.trecho },
              { onSuccess: () => setGrifo(null) },
            )
          }}
        />
      ) : null}

      <EditorChatBar
        chatInput={chatInput}
        onChange={onChatChange}
        highlightAtivo={highlightAtivo}
        iconesJuris={iconesJuris}
        onToggleHighlight={onToggleHighlight}
        onToggleIcones={onToggleIcones}
        podeElaborar={Boolean(elaboracao.elaboracaoId) && !elaboracao.gerarMinuta.isPending}
        elaborando={elaboracao.gerarMinuta.isPending}
        onElaborar={() => elaboracao.gerarMinuta.mutate()}
        podeConversar={Boolean(versaoMaisRecente) && !elaboracao.editarMinuta.isPending}
        enviandoChat={elaboracao.editarMinuta.isPending}
        onEnviarChat={() => {
          const instrucao = chatInput.trim()
          if (!instrucao) {
            return
          }
          elaboracao.editarMinuta.mutate(
            { instrucao },
            { onSuccess: () => onChatChange('') },
          )
        }}
        erro={erroGerar ?? erroEditar}
      />
    </div>
  )
}
