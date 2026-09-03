import type { CSSProperties } from 'react'
import { EditorContent, type Editor } from '@tiptap/react'
import { ScrollArea } from '#/components/ui/scroll-area'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import './minuta-editor.css'

interface DocumentViewerProps {
  editor: Editor | null
  editando: boolean
  carregando: boolean
  fonte: string
  tamanho: string
  espacamento: string
}

export function DocumentViewer({
  editor,
  editando,
  carregando,
  fonte,
  tamanho,
  espacamento,
}: DocumentViewerProps) {
  return (
    <ScrollArea className="flex-1 min-h-0">
      <div
        className={`minuta-editor mx-auto w-full max-w-[960px] my-6 rounded-sm shadow-sm border transition-all duration-200 bg-white ${
          editando ? 'is-editing border-[#2563EB] ring-2 ring-[#2563EB]/15' : 'is-readonly border-[#E5E7EB]'
        }`}
        style={
          {
            '--minuta-font': fonte,
            '--minuta-size': tamanho,
            '--minuta-line': espacamento,
          } as CSSProperties
        }
      >
        <div className="flex items-center justify-between px-10 py-3 border-b border-[#F3F4F6]">
          <span className="text-[10px] font-semibold text-[#9CA3AF] tracking-widest uppercase">
            AdvogAtiva — Minuta processual
          </span>
          {editando ? (
            <span className="text-[10px] font-semibold text-[#15803D] bg-[#F0FDF4] border border-[#BBF7D0] rounded-md px-2 py-0.5">
              Modo edição ativo
            </span>
          ) : (
            <span className="text-[10px] font-semibold text-[#6B7280]">
              Modo leitura e IA (clique em Editar p/ alterar)
            </span>
          )}
        </div>

        <div className="px-12 py-10 min-h-[420px]">
          {carregando ? (
            <div className="min-h-[200px] flex flex-col">
              <EstadoCarregando mensagem="Carregando cabeçalho do processo…" />
            </div>
          ) : editor ? (
            <EditorContent editor={editor} />
          ) : null}
        </div>
      </div>
    </ScrollArea>
  )
}
