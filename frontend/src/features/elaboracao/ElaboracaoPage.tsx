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
import {
  CAMPOS_MANUAIS_VAZIOS,
  camposDeCapa,
  capaComCampos,
  processoDeDadosManuais,
  type CamposManuais,
} from './elaboracao.manual'
import { modelosPeca } from './elaboracao.mock'
import { useAtualizarElaboracao, useElaboracao } from './elaboracoes.queries'
import type { ElaboracaoDetalhe } from './elaboracoes.types'
import {
  adicionarVersao,
  chaveVersoesElaboracao,
  lerVersoesDaElaboracao,
  type VersaoMinuta,
} from './elaboracao.versoes'

interface ElaboracaoPageProps {
  elaboracaoId: string
}

export function ElaboracaoPage({ elaboracaoId }: ElaboracaoPageProps) {
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
  const [erroPeca, setErroPeca] = useState<string | null>(null)
  const [campos, setCampos] = useState<CamposManuais>(CAMPOS_MANUAIS_VAZIOS)
  const editorRef = useRef<Editor | null>(null)
  const camposRef = useRef(campos)
  const capaRef = useRef<ElaboracaoDetalhe | undefined>(undefined)
  const salvarTimer = useRef<number | null>(null)
  const camposOrigem = useRef<string | null>(null)
  const onEditorChange = useCallback((editor: Editor | null) => {
    editorRef.current = editor
  }, [])

  const capaQuery = useElaboracao(elaboracaoId)
  const capa = capaQuery.data
  const atualizar = useAtualizarElaboracao(elaboracaoId)
  const processoId = capa?.processo_id ?? null

  const processoQuery = useQuery({
    queryKey: processoDetalheQueryKey(processoId ?? 'sem-processo'),
    queryFn: () => buscarProcesso(processoId as string),
    enabled: processoId !== null,
  })

  const pecaNome = modelosPeca.find((m) => m.id === pecaSelecionada)?.nome ?? 'Contestação'
  const semProcesso = Boolean(capa && !capa.tem_processo)
  capaRef.current = capa
  const processo = semProcesso
    ? capa
      ? processoDeDadosManuais(capaComCampos(capa, campos))
      : null
    : (processoQuery.data ?? null)

  const gravarCampos = useCallback(
    async (proximos: CamposManuais) => {
      const atual = capaRef.current
      if (!atual || atual.tem_processo || !atual.manual) {
        return
      }
      try {
        await atualizar.mutateAsync({
          manual: {
            titulo: atual.manual.titulo,
            nu_processo: proximos.nu_processo,
            parte_ativa: proximos.parte_ativa,
            parte_passiva: proximos.parte_passiva,
            classe: atual.manual.classe ?? undefined,
            assunto: atual.manual.assunto ?? undefined,
            foro_vara: proximos.foro_vara,
            valor_causa: proximos.valor_causa,
            juiz: atual.manual.juiz ?? undefined,
          },
        })
      } catch (falha) {
        setErroPeca(
          mensagemDeErro(falha, {
            401: 'Sessão expirada. Entre novamente.',
            422: 'Confira os dados do processo.',
          }),
        )
      }
    },
    [atualizar],
  )

  function agendarCampos(proximos: CamposManuais) {
    camposRef.current = proximos
    setCampos(proximos)
    setErroPeca(null)
    if (salvarTimer.current !== null) {
      window.clearTimeout(salvarTimer.current)
    }
    salvarTimer.current = window.setTimeout(() => {
      void gravarCampos(proximos)
    }, 450)
  }

  function gravarCamposAgora() {
    if (salvarTimer.current === null) {
      return
    }
    window.clearTimeout(salvarTimer.current)
    salvarTimer.current = null
    void gravarCampos(camposRef.current)
  }

  useEffect(() => {
    if (capa?.peca) {
      setPecaSelecionada(capa.peca)
    }
  }, [capa?.id, capa?.peca])

  useEffect(() => {
    if (!capa || capa.tem_processo || capa.id === camposOrigem.current) {
      return
    }
    camposOrigem.current = capa.id
    const iniciais = camposDeCapa(capa)
    camposRef.current = iniciais
    setCampos(iniciais)
  }, [capa])

  useEffect(() => {
    return () => {
      if (salvarTimer.current !== null) {
        window.clearTimeout(salvarTimer.current)
      }
    }
  }, [])

  useEffect(() => {
    const lista = lerVersoesDaElaboracao(
      (chave) => localStorage.getItem(chave),
      elaboracaoId,
      processoId,
      pecaSelecionada,
    )
    setVersoes(lista)
    setVersaoAtivaId(null)
  }, [elaboracaoId, processoId, pecaSelecionada])

  async function trocarPeca(proxima: string) {
    const anterior = pecaSelecionada
    setPecaSelecionada(proxima)
    setErroPeca(null)
    if (salvarTimer.current !== null) {
      window.clearTimeout(salvarTimer.current)
      salvarTimer.current = null
    }
    const nomeAnterior = modelosPeca.find((item) => item.id === anterior)?.nome
    const nomeNovo = modelosPeca.find((item) => item.id === proxima)?.nome ?? 'Peça'
    const tituloAtual = capa?.manual?.titulo?.trim()
    const titulo = !tituloAtual || tituloAtual === nomeAnterior ? nomeNovo : tituloAtual
    try {
      await atualizar.mutateAsync(
        semProcesso && capa?.manual
          ? {
              peca: proxima,
              manual: {
                titulo,
                nu_processo: camposRef.current.nu_processo,
                parte_ativa: camposRef.current.parte_ativa,
                parte_passiva: camposRef.current.parte_passiva,
                classe: capa.manual.classe ?? undefined,
                assunto: capa.manual.assunto ?? undefined,
                foro_vara: camposRef.current.foro_vara,
                valor_causa: camposRef.current.valor_causa,
                juiz: capa.manual.juiz ?? undefined,
              },
            }
          : { peca: proxima },
      )
    } catch (falha) {
      setPecaSelecionada(anterior)
      setErroPeca(
        mensagemDeErro(falha, {
          409: 'Já existe uma elaboração dessa peça neste processo.',
          401: 'Sessão expirada. Entre novamente.',
        }),
      )
    }
  }

  const onSalvarVersao = useCallback(() => {
    const html = editorRef.current?.getHTML()?.trim()
    if (!html) {
      return
    }
    const lista = adicionarVersao(versoes, html, new Date())
    setVersoes(lista)
    setVersaoAtivaId(lista[0]?.id ?? null)
    localStorage.setItem(chaveVersoesElaboracao(elaboracaoId), JSON.stringify(lista))
    void atualizar.mutateAsync({}).catch(() => undefined)
  }, [versoes, elaboracaoId, atualizar])

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

  const carregando = capaQuery.isLoading || (processoId !== null && processoQuery.isLoading)
  const erro = capaQuery.isError
    ? mensagemDeErro(capaQuery.error, {
        401: 'Sessão expirada. Entre novamente.',
        404: 'Elaboração não encontrada.',
      })
    : processoQuery.isError
      ? mensagemDeErro(processoQuery.error, {
          401: 'Sessão expirada. Entre novamente.',
          404: 'Processo não encontrado.',
        })
      : null
  const numeroManual = campos.nu_processo.trim()
  const rotuloProcesso = semProcesso
    ? numeroManual
      ? formatarNumeroCnj(numeroManual)
      : 'Sem processo'
    : processo
      ? formatarNumeroCnj(processo.nu_processo)
      : null

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
          onClick={() => navigate({ to: '/elaboracoes' })}
          className="h-8 px-2 text-[12px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Voltar
        </Button>

        <div className="w-px h-4 bg-[#E5E7EB]" />

        <div className="flex items-center gap-2 min-w-0">
          <Scale className="w-3.5 h-3.5 text-[#9CA3AF] shrink-0" />
          <span className="text-[12px] text-[#6B7280] truncate inline-flex items-center gap-1.5">
            {rotuloProcesso ? (
              rotuloProcesso
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

        {erroPeca ? <p className="text-[12px] text-[#B91C1C] truncate">{erroPeca}</p> : null}

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
        {erro ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
            <p className="text-sm text-[#6B7280] text-center">{erro}</p>
            <Link to="/elaboracoes" className="text-[13px] font-semibold text-[#2563EB] hover:underline">
              Voltar às elaborações
            </Link>
          </div>
        ) : (
          <>
            <LeftPanel
              collapsed={leftCollapsed}
              onToggle={() => setLeftCollapsed((v) => !v)}
              pecaSelecionada={pecaSelecionada}
              onPecaChange={(id) => {
                void trocarPeca(id)
              }}
              processo={processo}
              carregando={carregando}
              semProcesso={semProcesso}
              campos={campos}
              onCampos={agendarCampos}
              onCamposBlur={gravarCamposAgora}
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
              processo={processo}
              carregando={carregando}
              onEditorChange={onEditorChange}
            />

            <RightPanel
              collapsed={rightCollapsed}
              onToggle={() => setRightCollapsed((v) => !v)}
              processo={processo}
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
