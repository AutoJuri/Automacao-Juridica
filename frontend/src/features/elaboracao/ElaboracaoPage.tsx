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
import { sanitizarHtmlMinuta } from './elaboracao.sanitize'
import { useElaboracao, useSugestaoPeca } from './useElaboracao'

interface ElaboracaoPageProps {
  processoId: string
  /** `peca` que veio na URL (query param) quando o advogado chegou pelo
   * card "Ação sugerida" do cabeçalho do processo — ADR-016 Fase 1. */
  pecaSugeridaNaUrl?: string | null
}

function pecaValida(id: string | null | undefined): id is string {
  return Boolean(id) && modelosPeca.some((m) => m.id === id)
}

export function ElaboracaoPage({ processoId, pecaSugeridaNaUrl = null }: ElaboracaoPageProps) {
  const navigate = useNavigate()
  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)
  const [pecaSelecionada, setPecaSelecionada] = useState(
    pecaValida(pecaSugeridaNaUrl) ? pecaSugeridaNaUrl : modelosPeca[0].id,
  )
  const [editando, setEditando] = useState(false)
  const [highlightAtivo, setHighlightAtivo] = useState(true)
  const [iconesJuris, setIconesJuris] = useState(false)
  const [chatInput, setChatInput] = useState('')
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

  const elaboracao = useElaboracao(processoId, pecaSelecionada, Boolean(processo))

  // Mesma query (e mesma chave) que o cabeçalho do processo já buscou antes
  // de navegar pra aqui — cache quente na maioria das vezes. Serve tanto de
  // fallback (navegação direta/bookmark sem `peca` na URL) quanto de fonte
  // da explicação exibida no seletor. Só é aplicada ao `pecaSelecionada`
  // uma vez: depois que o advogado troca manualmente, a sugestão nunca mais
  // sobrescreve o seletor (ADR-016 Fase 1).
  const sugestaoAplicadaRef = useRef(pecaValida(pecaSugeridaNaUrl))
  const sugestaoPecaQuery = useSugestaoPeca(processoId, Boolean(processo))

  useEffect(() => {
    if (sugestaoAplicadaRef.current) return
    const sugerida = sugestaoPecaQuery.data?.peca
    if (pecaValida(sugerida)) {
      sugestaoAplicadaRef.current = true
      setPecaSelecionada(sugerida)
    }
  }, [sugestaoPecaQuery.data])

  function onPecaChange(id: string) {
    sugestaoAplicadaRef.current = true // advogado assumiu o controle — não sobrescreve mais
    setPecaSelecionada(id)
  }

  // Reaplica a versão mais recente no editor quando ela chega por uma ação
  // de IA (Elaborar/chat/grifo) sem trocar de peça — trocar de peça já é
  // coberto pelo reset por `chave` dentro de `useMinutaEditor`.
  const chaveAtualRef = useRef('')
  const versaoAplicadaRef = useRef<string | null>(null)
  const versaoMaisRecente = elaboracao.versoesQuery.data?.[0] ?? null

  useEffect(() => {
    const chaveAtual = `${processoId}:${pecaSelecionada}`
    if (chaveAtualRef.current !== chaveAtual) {
      chaveAtualRef.current = chaveAtual
      versaoAplicadaRef.current = versaoMaisRecente?.id ?? null
      setVersaoAtivaId(versaoMaisRecente?.id ?? null)
      return
    }
    if (!versaoMaisRecente || !editorRef.current) {
      return
    }
    if (versaoAplicadaRef.current === versaoMaisRecente.id) {
      return
    }
    versaoAplicadaRef.current = versaoMaisRecente.id
    editorRef.current.commands.setContent(sanitizarHtmlMinuta(versaoMaisRecente.conteudo_html))
    setVersaoAtivaId(versaoMaisRecente.id)
  }, [processoId, pecaSelecionada, versaoMaisRecente])

  const onRestaurarVersao = useCallback(
    (id: string) => {
      const versao = elaboracao.versoesQuery.data?.find((item) => item.id === id)
      if (!versao || !editorRef.current) {
        return
      }
      editorRef.current.commands.setContent(sanitizarHtmlMinuta(versao.conteudo_html))
      versaoAplicadaRef.current = id
      setVersaoAtivaId(id)
    },
    [elaboracao.versoesQuery.data],
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
              onPecaChange={onPecaChange}
              sugestaoPeca={
                sugestaoPecaQuery.data?.peca === pecaSelecionada
                  ? sugestaoPecaQuery.data
                  : null
              }
              processo={processo ?? null}
              carregando={detalheQuery.isLoading}
              fatosExtras={elaboracao.sessaoQuery.data?.fatos_extras ?? null}
              onSalvarFatosExtras={(texto) => elaboracao.salvarFatosExtras.mutate(texto)}
              salvandoFatosExtras={elaboracao.salvarFatosExtras.isPending}
              fatosExtrasDesabilitado={!elaboracao.elaboracaoId}
              elaboracaoId={elaboracao.elaboracaoId}
              estiloAtual={elaboracao.sessaoQuery.data?.estilo_perfil ?? null}
              onSalvarEstilo={(texto) => elaboracao.definirEstilo.mutate(texto)}
              salvandoEstilo={elaboracao.definirEstilo.isPending}
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
              elaboracao={elaboracao}
            />

            <RightPanel
              collapsed={rightCollapsed}
              onToggle={() => setRightCollapsed((v) => !v)}
              processo={processo ?? null}
              versoes={elaboracao.versoesQuery.data ?? []}
              versaoAtivaId={versaoAtivaId}
              carregandoVersoes={elaboracao.versoesQuery.isLoading}
              onRestaurarVersao={onRestaurarVersao}
            />
          </>
        )}
      </div>
    </div>
  )
}
