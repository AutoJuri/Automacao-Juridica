import { useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Copy,
  Download,
  FileText,
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
import { copiarTexto, formatarNumeroCnj, imprimirTexto } from './processos.format'
import { formatarDataSP } from './processos.dates'
import type { MovimentacaoPublica } from './processos.types'

interface VisualizadorPdfModalProps {
  aberto: boolean
  onFechar: () => void
  movimentacao: MovimentacaoPublica
  numeroProcesso: string | null
  hrefDocumento: string | null
}

const ZOOM_MIN = 75
const ZOOM_MAX = 150
const ZOOM_PASSO = 25

export function VisualizadorPdfModal({
  aberto,
  onFechar,
  movimentacao,
  numeroProcesso,
  hrefDocumento,
}: VisualizadorPdfModalProps) {
  const [zoom, setZoom] = useState(100)
  const [copiado, setCopiado] = useState(false)
  const titulo = movimentacao.titulo?.trim() || 'Movimentação'
  const corpo = [titulo, movimentacao.descricao.trim()].filter(Boolean).join('\n\n')
  const numero = formatarNumeroCnj(numeroProcesso)
  const arquivo = `${titulo}.pdf`

  async function copiar() {
    const ok = await copiarTexto(corpo)
    if (!ok) {
      return
    }
    setCopiado(true)
    window.setTimeout(() => setCopiado(false), 2000)
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
              onClick={() => imprimirTexto(titulo, corpo)}
              className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-medium text-[#374151] hover:bg-[#F8F9FC]"
            >
              <Printer className="w-3.5 h-3.5" aria-hidden />
              Imprimir
            </button>
            {hrefDocumento ? (
              <a
                href={hrefDocumento}
                target="_blank"
                rel="noreferrer"
                title="Abre o documento no e-SAJ. O PDF não é baixado pelo nosso servidor."
                className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white hover:bg-[#1D4ED8]"
              >
                <Download className="w-3.5 h-3.5" aria-hidden />
                Baixar PDF
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

        <div className="flex items-center justify-between border-t border-[#E5E7EB] px-5 py-2.5">
          <p className="text-[11px] text-[#6B7280]">
            Texto da movimentação. O PDF original, quando existir, abre no e-SAJ.
          </p>
          <div className="inline-flex items-center gap-2 text-[11px] text-[#6B7280]">
            <ChevronLeft className="w-4 h-4 opacity-40" aria-hidden />
            <span className="tabular-nums">Página 1 de 1</span>
            <ChevronRight className="w-4 h-4 opacity-40" aria-hidden />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
