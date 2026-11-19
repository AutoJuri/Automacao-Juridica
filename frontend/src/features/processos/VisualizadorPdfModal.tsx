import { useRef, useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Copy,
  Download,
  ExternalLink,
  FileText,
  Loader2,
  Printer,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from '#/components/ui/dialog'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { copiarTexto, formatarNumeroCnj, imprimirTexto } from './processos.format'
import { formatarDataSP } from './processos.dates'
import { usePdfDaMovimentacao } from './documento.api'
import type { MovimentacaoPublica } from './processos.types'

interface VisualizadorPdfModalProps {
  aberto: boolean
  onFechar: () => void
  movimentacao: MovimentacaoPublica
  numeroProcesso: string | null
  hrefDocumento: string | null
  /**
   * Processo salvo na plataforma. Com ele, o PDF vem pelo nosso servidor.
   * Sem ele (consulta pública), o modal mostra só o texto e o link do e-SAJ.
   */
  processoId?: string | null
}

type Vista = 'pdf' | 'texto'

const ZOOM_MIN = 75
const ZOOM_MAX = 150
const ZOOM_PASSO = 25

const ERROS_PDF: Record<number, string> = {
  404: 'Documento não encontrado.',
  409: 'A sessão do e-SAJ expirou. Reconecte em Configurações e tente de novo.',
  422: 'O e-SAJ não entregou um PDF para este documento.',
  429: 'O e-SAJ está limitando os acessos. Tente novamente em alguns minutos.',
  502: 'O e-SAJ não respondeu. Tente novamente.',
}

export function VisualizadorPdfModal({
  aberto,
  onFechar,
  movimentacao,
  numeroProcesso,
  hrefDocumento,
  processoId = null,
}: VisualizadorPdfModalProps) {
  const [zoom, setZoom] = useState(100)
  const [copiado, setCopiado] = useState(false)
  const [vista, setVista] = useState<Vista>('pdf')
  const quadroRef = useRef<HTMLIFrameElement>(null)

  const titulo = movimentacao.titulo?.trim() || 'Movimentação'
  const corpo = [titulo, movimentacao.descricao.trim()].filter(Boolean).join('\n\n')
  const numero = formatarNumeroCnj(numeroProcesso)
  const arquivo = `${titulo}.pdf`

  // Só há PDF para buscar quando o CPO deu o link direto do documento.
  const podeVerPdf = processoId !== null && Boolean(movimentacao.url_documento)
  const pdf = usePdfDaMovimentacao(processoId, movimentacao.id, aberto && podeVerPdf)
  const mostrandoPdf = podeVerPdf && vista === 'pdf'

  async function copiar() {
    const ok = await copiarTexto(corpo)
    if (!ok) {
      return
    }
    setCopiado(true)
    window.setTimeout(() => setCopiado(false), 2000)
  }

  function imprimir() {
    if (mostrandoPdf && pdf.url) {
      quadroRef.current?.contentWindow?.print()
      return
    }
    imprimirTexto(titulo, corpo)
  }

  return (
    <Dialog open={aberto} onOpenChange={(proximo) => !proximo && onFechar()}>
      <DialogContent
        showCloseButton={false}
        className="flex max-h-[90vh] w-[min(960px,calc(100%-2rem))] max-w-none flex-col gap-0 overflow-hidden rounded-2xl border border-[#E5E7EB] bg-white p-0 shadow-2xl sm:max-w-none"
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#E5E7EB] px-5 py-4">
          <div className="flex items-start gap-3 min-w-0">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB] shrink-0">
              <FileText className="w-4 h-4" aria-hidden />
            </span>
            <div className="min-w-0">
              <DialogTitle className="text-[15px] font-semibold text-[#111827] leading-snug truncate">
                {arquivo}
              </DialogTitle>
              <DialogDescription className="text-[12px] text-[#6B7280] mt-0.5">
                Processo: {numero} • {formatarDataSP(movimentacao.data_movimentacao)}
              </DialogDescription>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {podeVerPdf ? (
              <div
                role="group"
                aria-label="O que mostrar"
                className="inline-flex h-8 items-center rounded-lg border border-[#E5E7EB] bg-white p-0.5 text-[12px] font-medium"
              >
                {(['pdf', 'texto'] as const).map((opcao) => (
                  <button
                    key={opcao}
                    type="button"
                    onClick={() => setVista(opcao)}
                    aria-pressed={vista === opcao}
                    className={`h-full rounded-md px-2.5 ${
                      vista === opcao
                        ? 'bg-[#111827] text-white'
                        : 'text-[#374151] hover:bg-[#F3F4F6]'
                    }`}
                  >
                    {opcao === 'pdf' ? 'PDF' : 'Texto'}
                  </button>
                ))}
              </div>
            ) : null}

            {!mostrandoPdf ? (
              <div className="hidden sm:inline-flex items-center gap-1 rounded-lg border border-[#E5E7EB] bg-white px-1.5 h-8">
                <button
                  type="button"
                  onClick={() => setZoom((z) => Math.max(ZOOM_MIN, z - ZOOM_PASSO))}
                  disabled={zoom <= ZOOM_MIN}
                  aria-label="Diminuir zoom"
                  className="inline-flex h-6 w-6 items-center justify-center text-[#6B7280] hover:text-[#111827] disabled:opacity-40"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-[11px] font-medium text-[#374151] tabular-nums w-10 text-center">
                  {zoom}%
                </span>
                <button
                  type="button"
                  onClick={() => setZoom((z) => Math.min(ZOOM_MAX, z + ZOOM_PASSO))}
                  disabled={zoom >= ZOOM_MAX}
                  aria-label="Aumentar zoom"
                  className="inline-flex h-6 w-6 items-center justify-center text-[#6B7280] hover:text-[#111827] disabled:opacity-40"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : null}

            <button
              type="button"
              onClick={() => void copiar()}
              className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-medium text-[#374151] hover:bg-[#F8F9FC]"
            >
              <Copy className="w-3.5 h-3.5" aria-hidden />
              {copiado ? 'Copiado' : 'Copiar texto'}
            </button>
            <button
              type="button"
              onClick={imprimir}
              disabled={mostrandoPdf && !pdf.url}
              className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-medium text-[#374151] hover:bg-[#F8F9FC] disabled:text-[#9CA3AF]"
            >
              <Printer className="w-3.5 h-3.5" aria-hidden />
              Imprimir
            </button>
            {pdf.url ? (
              <a
                href={pdf.url}
                download={arquivo}
                className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white hover:bg-[#1D4ED8]"
              >
                <Download className="w-3.5 h-3.5" aria-hidden />
                Baixar PDF
              </a>
            ) : hrefDocumento ? (
              <a
                href={hrefDocumento}
                target="_blank"
                rel="noreferrer"
                title="Abre o documento no e-SAJ, no seu navegador."
                className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white hover:bg-[#1D4ED8]"
              >
                <ExternalLink className="w-3.5 h-3.5" aria-hidden />
                Abrir no e-SAJ
              </a>
            ) : (
              <span
                title="Documento ainda não disponível para abrir no e-SAJ"
                className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#E5E7EB] px-3 text-[12px] font-semibold text-[#9CA3AF]"
              >
                <Download className="w-3.5 h-3.5" aria-hidden />
                Baixar PDF
              </span>
            )}
            <button
              type="button"
              onClick={onFechar}
              aria-label="Fechar visualizador"
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {mostrandoPdf ? (
          <div className="h-[75vh] min-h-0 bg-[#F3F4F6]">
            {pdf.carregando ? (
              <div
                role="status"
                className="flex h-full flex-col items-center justify-center gap-3 text-[13px] text-[#6B7280]"
              >
                <Loader2 className="w-5 h-5 animate-spin" aria-hidden />
                Buscando o documento no e-SAJ…
              </div>
            ) : pdf.url ? (
              <iframe
                ref={quadroRef}
                src={pdf.url}
                title={`PDF: ${titulo}`}
                className="h-full w-full border-0"
              />
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
                <p role="alert" className="max-w-md text-[13px] leading-relaxed text-[#374151]">
                  {mensagemDeErro(pdf.erro, ERROS_PDF)}
                </p>
                <button
                  type="button"
                  onClick={() => setVista('texto')}
                  className="inline-flex h-8 items-center rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-medium text-[#374151] hover:bg-[#F8F9FC]"
                >
                  Ver o texto da movimentação
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-y-auto bg-[#F3F4F6] px-6 py-6">
            <article
              className="mx-auto max-w-[720px] bg-white shadow-md rounded-sm px-10 py-12"
              style={{ fontSize: `${zoom}%` }}
            >
              <p className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#6B7280] mb-6">
                Movimentação coletada do CPO
              </p>
              <h2 className="text-[16px] font-bold text-[#111827] leading-snug mb-4">{titulo}</h2>
              <p className="text-[13px] text-[#374151] leading-relaxed whitespace-pre-wrap">
                {movimentacao.descricao.trim() || 'Sem texto adicional nesta movimentação.'}
              </p>
            </article>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-[#E5E7EB] px-5 py-2.5">
          <p className="text-[11px] text-[#6B7280]">
            {mostrandoPdf
              ? 'O PDF vem do e-SAJ pela sua sessão e não fica salvo na plataforma.'
              : 'Texto da movimentação. O PDF original, quando existir, abre no e-SAJ.'}
          </p>
          {mostrandoPdf ? null : (
            <div className="inline-flex items-center gap-2 text-[11px] text-[#6B7280]">
              <ChevronLeft className="w-4 h-4 opacity-40" aria-hidden />
              <span className="tabular-nums">Página 1 de 1</span>
              <ChevronRight className="w-4 h-4 opacity-40" aria-hidden />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
