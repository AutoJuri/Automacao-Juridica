import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { EditorContent, type Editor } from '@tiptap/react'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { totalDePaginas } from './paginacao'
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
  const viewportRef = useRef<HTMLDivElement>(null)
  const [total, setTotal] = useState(1)
  const [atual, setAtual] = useState(1)

  useEffect(() => {
    if (!editor) {
      return
    }
    const ler = () => setTotal(totalDePaginas(editor))
    ler()
    editor.on('transaction', ler)
    return () => {
      editor.off('transaction', ler)
    }
  }, [editor])

  useEffect(() => {
    const viewport = viewportRef.current
    if (!viewport) {
      return
    }
    const ler = () => {
      const limite = viewport.getBoundingClientRect().top + 48
      let pagina = 1
      viewport.querySelectorAll<HTMLElement>('[data-folha]').forEach((marca) => {
        const numero = Number(marca.dataset.folha)
        if (Number.isFinite(numero) && marca.getBoundingClientRect().top <= limite) {
          pagina = numero
        }
      })
      setAtual(pagina)
    }
    ler()
    viewport.addEventListener('scroll', ler, { passive: true })
    return () => viewport.removeEventListener('scroll', ler)
  }, [total, editor, carregando])

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div ref={viewportRef} className="min-h-0 flex-1 overflow-auto bg-[#E5E7EB]">
        <div
          className={`minuta-editor py-6 ${editando ? 'is-editing' : 'is-readonly'}`}
          style={
            {
              '--minuta-font': fonte,
              '--minuta-size': tamanho,
              '--minuta-line': espacamento,
            } as CSSProperties
          }
        >
          {carregando ? (
            <div className="mx-auto flex min-h-[297mm] w-[210mm] items-center bg-white shadow-sm">
              <EstadoCarregando mensagem="Carregando cabeçalho do processo…" />
            </div>
          ) : editor ? (
            <EditorContent editor={editor} />
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 items-center justify-between border-t border-[#E5E7EB] bg-white px-4 py-1.5">
        <span className="text-[11px] text-[#6B7280]">{editando ? 'Modo edição' : 'Modo leitura'}</span>
        <span className="text-[11px] font-medium text-[#374151]">
          Página {Math.min(atual, Math.max(total, 1))} de {Math.max(total, 1)}
        </span>
      </div>
    </div>
  )
}