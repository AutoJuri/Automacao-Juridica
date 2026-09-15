import { useState } from 'react'
import { Copy, FileText } from 'lucide-react'
import { copiarTexto } from './processos.format'
import { formatarDataSP } from './processos.dates'
import type { MovimentacaoPublica } from './processos.types'
import { hrefDocumentoMovimentacao } from './processos.urls'
import { VisualizadorPdfModal } from './VisualizadorPdfModal'

interface DetalheMovimentacaoProps {
  movimentacao: MovimentacaoPublica | null
  urlCpo: string | null
  numeroProcesso: string | null
  total: number
}

export function DetalheMovimentacao({
  movimentacao,
  urlCpo,
  numeroProcesso,
  total,
}: DetalheMovimentacaoProps) {
  const [pdfAberto, setPdfAberto] = useState(false)
  const [copiado, setCopiado] = useState(false)

  const hrefDocumento = movimentacao
    ? hrefDocumentoMovimentacao(
        movimentacao.tem_documento,
        movimentacao.url_documento,
        urlCpo,
      )
    : null
  const textoCompleto = movimentacao
    ? [movimentacao.titulo?.trim(), movimentacao.descricao.trim()].filter(Boolean).join('\n\n')
    : ''

  async function copiar() {
    const ok = await copiarTexto(textoCompleto)
    if (!ok) {
      return
    }
    setCopiado(true)
    window.setTimeout(() => setCopiado(false), 2000)
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="shrink-0 flex items-start justify-between gap-3 px-5 pt-5 pb-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
            Detalhe da movimentação
            {total > 0 ? ` (${movimentacao ? '1' : '0'}/${total})` : ''}
          </p>
          <p className="text-[11px] text-[#9CA3AF] mt-1">
            Conteúdo oficial correspondente à fase
          </p>
        </div>
        {movimentacao ? (
          <div className="flex items-center gap-2 shrink-0">
            {movimentacao.tem_documento ? (
              <button
                type="button"
                onClick={() => setPdfAberto(true)}
                className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#111827] px-3 text-[11px] font-semibold text-white hover:bg-[#1F2937]"
              >
                <FileText className="w-3.5 h-3.5" aria-hidden />
                Visualizar PDF
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => void copiar()}
              disabled={!textoCompleto}
              className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[11px] font-semibold text-[#374151] hover:bg-[#F8F9FC] disabled:text-[#9CA3AF]"
            >
              <Copy className="w-3.5 h-3.5" aria-hidden />
              {copiado ? 'Copiado' : 'Copiar'}
            </button>
          </div>
        ) : null}
      </div>

      <div className="flex-1 min-h-0 px-5 pb-5">
        {movimentacao ? (
          <div className="h-full overflow-y-auto rounded-xl border border-[#E5E7EB] bg-[#FAFAFA] px-5 py-4">
            <p className="text-[11px] font-medium text-[#6B7280] tabular-nums mb-2">
              {formatarDataSP(movimentacao.data_movimentacao)}
            </p>
            <p className="text-[14px] font-semibold text-[#111827] leading-snug mb-3">
              {movimentacao.titulo?.trim() || 'Movimentação'}
            </p>
            <p className="text-[13px] text-[#374151] leading-relaxed whitespace-pre-wrap">
              {movimentacao.descricao.trim() || 'Sem texto adicional nesta movimentação.'}
            </p>
          </div>
        ) : (
          <div className="h-full rounded-xl border border-dashed border-[#E5E7EB] bg-[#FAFAFA] flex items-center justify-center px-6 text-center">
            <p className="text-[13px] text-[#9CA3AF] leading-relaxed">
              Selecione uma movimentação à esquerda para ver o texto completo.
            </p>
          </div>
        )}
      </div>

      {movimentacao ? (
        <VisualizadorPdfModal
          aberto={pdfAberto}
          onFechar={() => setPdfAberto(false)}
          movimentacao={movimentacao}
          numeroProcesso={numeroProcesso}
          hrefDocumento={hrefDocumento}
        />
      ) : null}
    </div>
  )
}
