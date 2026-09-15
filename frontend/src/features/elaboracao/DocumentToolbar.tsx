import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  Copy,
  FileDown,
  FileText,
  Italic,
  Pencil,
  Redo2,
  Scissors,
  Strikethrough,
  Underline,
  Undo2,
} from 'lucide-react'
import type { Editor } from '@tiptap/react'
import { Button } from '#/components/ui/button'
import {
  ESPACAMENTOS_MINUTA,
  FONTES_MINUTA,
  TAMANHOS_MINUTA,
} from './elaboracao.minuta'
import { alinhamentoDoNo, FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

interface DocumentActionsProps {
  editando: boolean
  onToggleEditar: () => void
  onCopiar: () => void
}

const ACAO_DESABILITADA = 'Exportação ainda não está em operação'

export function DocumentActions({ editando, onToggleEditar, onCopiar }: DocumentActionsProps) {
  return (
    <div className="flex items-center gap-1 flex-wrap justify-end">
      <AcaoIcone icon={Scissors} label="Extrair" />
      <button
        type="button"
        onClick={onCopiar}
        title="Copiar texto da minuta"
        className="h-8 px-2 inline-flex items-center gap-1.5 rounded-md text-[11px] text-[#6B7280] hover:bg-[#F3F4F6]"
      >
        <Copy className="w-3.5 h-3.5" />
        <span className="hidden xl:inline">Copiar</span>
      </button>
      <AcaoIcone icon={FileText} label="Word" />
      <AcaoIcone icon={FileDown} label="PDF" />

      <Button
        size="sm"
        onClick={onToggleEditar}
        className={
          editando
            ? 'h-8 px-3 text-[11px] font-semibold gap-1.5 bg-[#111827] hover:bg-[#1F2937] text-white ml-1'
            : 'h-8 px-3 text-[11px] font-semibold gap-1.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white ml-1'
        }
      >
        <Pencil className="w-3.5 h-3.5" />
        {editando ? 'Editando (salvar)' : 'Editar no documento'}
      </Button>
    </div>
  )
}

function AcaoIcone({
  icon: Icon,
  label,
}: {
  icon: typeof Copy
  label: string
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      disabled
      title={ACAO_DESABILITADA}
      className="h-8 px-2 text-[11px] gap-1.5 text-[#6B7280]"
    >
      <Icon className="w-3.5 h-3.5" />
      <span className="hidden xl:inline">{label}</span>
    </Button>
  )
}

interface DocumentFormatToolbarProps {
  editor: Editor | null
  editando: boolean
  fonte: string
  tamanho: string
  espacamento: string
  onFonte: (v: string) => void
  onTamanho: (v: string) => void
  onEspacamento: (v: string) => void
}

export function DocumentFormatToolbar({
  editor,
  editando,
  fonte,
  tamanho,
  espacamento,
  onFonte,
  onTamanho,
  onEspacamento,
}: DocumentFormatToolbarProps) {
  const ativo = Boolean(editor && editando)
  const alinhamento = editor
    ? alinhamentoDoNo(editor.state.selection.$from.parent.attrs.textAlign)
    : 'justify'

  return (
    <div className="flex items-center justify-center gap-1 flex-wrap px-4 py-2.5 border-b border-[#E5E7EB] bg-white shrink-0">
      <Ferramenta
        icon={Undo2}
        title="Desfazer (Ctrl+Z)"
        disabled={!ativo}
        onClick={() => editor?.chain().focus().undo().run()}
      />
      <Ferramenta
        icon={Redo2}
        title="Refazer (Ctrl+Y)"
        disabled={!ativo}
        onClick={() => editor?.chain().focus().redo().run()}
      />
      <div className="w-px h-5 bg-[#E5E7EB] mx-1.5" />
      <select
        disabled={!ativo}
        value={fonte}
        aria-label="Fonte"
        onChange={(e) => {
          onFonte(e.target.value)
          editor?.chain().focus().setFontFamily(e.target.value).run()
        }}
        className={`h-8 min-w-[10.5rem] rounded-md border border-[#E5E7EB] bg-white px-2.5 text-[13px] text-[#374151] disabled:opacity-50 ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      >
        {FONTES_MINUTA.map((item) => (
          <option key={item.rotulo} value={item.valor}>
            {item.rotulo}
          </option>
        ))}
      </select>
      <select
        disabled={!ativo}
        value={tamanho}
        aria-label="Tamanho da fonte"
        onChange={(e) => {
          onTamanho(e.target.value)
          editor?.chain().focus().setFontSize(e.target.value).run()
        }}
        className={`h-8 rounded-md border border-[#E5E7EB] bg-white px-2.5 text-[13px] text-[#374151] disabled:opacity-50 ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      >
        {TAMANHOS_MINUTA.map((item) => (
          <option key={item.valor} value={item.valor}>
            {item.rotulo}
          </option>
        ))}
      </select>
      <div className="w-px h-5 bg-[#E5E7EB] mx-1.5" />
      <Ferramenta
        icon={Bold}
        title="Negrito (Ctrl+B)"
        disabled={!ativo}
        ativo={editor?.isActive('bold')}
        onClick={() => editor?.chain().focus().toggleBold().run()}
      />
      <Ferramenta
        icon={Italic}
        title="Itálico (Ctrl+I)"
        disabled={!ativo}
        ativo={editor?.isActive('italic')}
        onClick={() => editor?.chain().focus().toggleItalic().run()}
      />
      <Ferramenta
        icon={Underline}
        title="Sublinhado (Ctrl+U)"
        disabled={!ativo}
        ativo={editor?.isActive('underline')}
        onClick={() => editor?.chain().focus().toggleUnderline().run()}
      />
      <Ferramenta
        icon={Strikethrough}
        title="Tachado"
        disabled={!ativo}
        ativo={editor?.isActive('strike')}
        onClick={() => editor?.chain().focus().toggleStrike().run()}
      />
      <div className="w-px h-5 bg-[#E5E7EB] mx-1.5" />
      <Ferramenta
        icon={AlignLeft}
        title="Alinhar à esquerda"
        disabled={!ativo}
        ativo={alinhamento === 'left'}
        onClick={() => editor?.chain().focus().setTextAlign('left').run()}
      />
      <Ferramenta
        icon={AlignCenter}
        title="Centralizar"
        disabled={!ativo}
        ativo={alinhamento === 'center'}
        onClick={() => editor?.chain().focus().setTextAlign('center').run()}
      />
      <Ferramenta
        icon={AlignRight}
        title="Alinhar à direita"
        disabled={!ativo}
        ativo={alinhamento === 'right'}
        onClick={() => editor?.chain().focus().setTextAlign('right').run()}
      />
      <Ferramenta
        icon={AlignJustify}
        title="Justificar (padrão jurídico)"
        disabled={!ativo}
        ativo={alinhamento === 'justify'}
        onClick={() => {
          if (alinhamento === 'justify') {
            editor?.chain().focus().setTextAlign('left').run()
            return
          }
          editor?.chain().focus().setTextAlign('justify').run()
        }}
      />
      <select
        disabled={!ativo}
        value={espacamento}
        aria-label="Espaçamento entre linhas"
        onChange={(e) => {
          onEspacamento(e.target.value)
          editor?.chain().focus().setLineHeight(e.target.value).run()
        }}
        className={`h-8 rounded-md border border-[#E5E7EB] bg-white px-2.5 text-[13px] text-[#374151] disabled:opacity-50 ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      >
        {ESPACAMENTOS_MINUTA.map((item) => (
          <option key={item.valor} value={item.valor}>
            {item.rotulo}
          </option>
        ))}
      </select>
    </div>
  )
}

function Ferramenta({
  icon: Icon,
  title,
  disabled,
  ativo = false,
  onClick,
}: {
  icon: typeof Bold
  title: string
  disabled: boolean
  ativo?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      title={disabled ? 'Entre em edição para usar a formatação' : title}
      onClick={onClick}
      className={[
        'h-8 w-8 inline-flex items-center justify-center rounded-md',
        ativo ? 'bg-[#EFF6FF] text-[#2563EB]' : 'text-[#4B5563] hover:bg-[#F3F4F6]',
        'disabled:opacity-40 disabled:hover:bg-transparent',
      ].join(' ')}
    >
      <Icon className="w-4 h-4" />
    </button>
  )
}
