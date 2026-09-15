import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import type { Editor } from '@tiptap/react'
import { ArrowLeft, Loader2, Scale } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { Navbar, NAVBAR_HEIGHT } from '#/features/processos/Navbar'
import { buscarProcesso } from '#/features/processos/processos.api'
import { processoDetalheQueryKey } from '#/features/processos/processos.constants'
import { formatarNumeroCnj } from '#/features/processos/processos.format'
import { LeftPanel } from './LeftPanel'
import { CenterPanel } from './CenterPanel'
import { RightPanel } from './RightPanel'
import { DocumentActions } from './DocumentToolbar'
import { modelosPeca } from './elaboracao.mock'
import {
  adicionarVersao,
  chaveVersoes,
  lerVersoes,
  type VersaoMinuta,
} from './elaboracao.versoes'

interface ElaboracaoPageProps {
  processoId: string
}

export function ElaboracaoPage({ processoId }: ElaboracaoPageProps) {
  const navigate = useNavigate()
  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)
  const [pecaSelecionada, setPecaSelecionada] = useState(modelosPeca[0].id)
  const [editando, setEditando] = useState(false)
  const [highlightAtivo, setHighlightAtivo] = useState(true)
  const [iconesJuris, setIconesJuris] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [versoes, setVersoes] = useState<VersaoMinuta[]>([])
  const [versaoAtivaId, setVersaoAtivaId] = useState<string | null>(null)
  const editorRef = useRef<Editor | null>(null)
  const onEditorChange = useCallback((editor: Editor | null) => {
    editorRef.current = editor
  }, [])

  const detalheQuery = useQuery({
    queryKey: processoDetalheQueryKey(processoId),
    queryFn: () => buscarProcesso(processoId),
  })

  const pecaNome = modelosPeca.find((m) => m.id === pecaSelecionada)?.nome ?? 'Contestação'
  const processo = detalheQuery.data

  useEffect(() => {
    const bruto = localStorage.getItem(chaveVersoes(processoId, pecaSelecionada))
    setVersoes(lerVersoes(bruto))
    setVersaoAtivaId(null)
  }, [processoId, pecaSelecionada])

  const onSalvarVersao = useCallback(() => {
    const html = editorRef.current?.getHTML()?.trim()
    if (!html) {
      return
    }
    const lista = adicionarVersao(versoes, html, new Date())
    setVersoes(lista)
    setVersaoAtivaId(lista[0]?.id ?? null)
    localStorage.setItem(chaveVersoes(processoId, pecaSelecionada), JSON.stringify(lista))
  }, [versoes, processoId, pecaSelecionada])

  const onRestaurarVersao = useCallback(
    (id: string) => {
      const versao = versoes.find((item) => item.id === id)
      if (!versao || !editorRef.current) {
        return
      }
      editorRef.current.commands.setContent(versao.html)
      setVersaoAtivaId(id)
      setEditando(true)
    },
    [versoes],
  )

  return (
    <div className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden">
      <Navbar />

      <div
        className="fixed left-0 right-0 z-40 flex items-center gap-3 px-5 bg-white border-b border-[#E5E7EB]"
        style={{ top: NAVBAR_HEIGHT, height: 48 }}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate({ to: '/' })}
          className="h-8 px-2 text-[12px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Voltar
        </Button>

        <div className="w-px h-4 bg-[#E5E7EB]" />

        <div className="flex items-center gap-2 min-w-0">
          <Scale className="w-3.5 h-3.5 text-[#9CA3AF] shrink-0" />
          <span className="text-[12px] text-[#6B7280] truncate inline-flex items-center gap-1.5">
            {processo ? (
              formatarNumeroCnj(processo.nu_processo)
            ) : (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#2563EB] shrink-0" aria-hidden />
                Carregando…
              </>
            )}
          </span>
          <span className="text-[#9CA3AF]">/</span>
          <span className="text-[12px] font-semibold text-[#111827] truncate">{pecaNome}</span>
        </div>

        <div className="flex-1" />

        <DocumentActions
          editando={editando}
          onToggleEditar={() => setEditando((v) => !v)}
          onCopiar={() => {
            const texto = editorRef.current?.getText()?.trim() ?? ''
            if (texto) {
              void navigator.clipboard.writeText(texto)
            }
          }}
        />
      </div>

      <div
        className="flex flex-1 overflow-hidden min-h-0"
        style={{ marginTop: NAVBAR_HEIGHT + 48 }}
      >
        {detalheQuery.isError ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
            <p className="text-sm text-[#6B7280] text-center">
              {mensagemDeErro(detalheQuery.error, {
                401: 'Sessão expirada. Entre novamente.',
                404: 'Processo não encontrado.',
              })}
            </p>
            <Link to="/" className="text-[13px] font-semibold text-[#2563EB] hover:underline">
              Voltar ao gabinete
            </Link>
          </div>
        ) : (
          <>
            <LeftPanel
              collapsed={leftCollapsed}
              onToggle={() => setLeftCollapsed((v) => !v)}
              pecaSelecionada={pecaSelecionada}
              onPecaChange={setPecaSelecionada}
              processo={processo ?? null}
              carregando={detalheQuery.isLoading}
            />

            <CenterPanel
              editando={editando}
              highlightAtivo={highlightAtivo}
              iconesJuris={iconesJuris}
              onToggleHighlight={setHighlightAtivo}
              onToggleIcones={setIconesJuris}
              chatInput={chatInput}
              onChatChange={setChatInput}
              pecaSelecionada={pecaSelecionada}
              processo={processo ?? null}
              carregando={detalheQuery.isLoading}
              onEditorChange={onEditorChange}
            />

            <RightPanel
              collapsed={rightCollapsed}
              onToggle={() => setRightCollapsed((v) => !v)}
              processo={processo ?? null}
              versoes={versoes}
              versaoAtivaId={versaoAtivaId}
              onSalvarVersao={onSalvarVersao}
              onRestaurarVersao={onRestaurarVersao}
            />
          </>
        )}
      </div>
    </div>
  )
}
