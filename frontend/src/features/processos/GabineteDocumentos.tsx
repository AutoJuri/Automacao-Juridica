import { Copy, FileText } from 'lucide-react'
import { Button } from '#/components/ui/button'
import type { Documento } from './processos.mock'

interface GabineteDocumentosProps {
  documentos: Documento[]
  ultimaMovimentacao: string
}

export function GabineteDocumentos({ documentos, ultimaMovimentacao }: GabineteDocumentosProps) {
  const doc = documentos[0]

  if (!doc) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-[#9CA3AF] text-sm">
        Nenhum documento disponível.
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
            Gabinete de Documentos ({documentos.length}/5)
          </p>
          <p className="text-[11px] text-[#9CA3AF] mt-1">
            Conteúdo oficial correspondente à fase
          </p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button
            size="sm"
            className="h-7 px-3 text-[11px] gap-1.5 bg-[#0D0F14] text-white hover:bg-[#1a1d26] rounded-md"
          >
            <FileText className="w-3 h-3" />
            PDF
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-3 text-[11px] gap-1.5 text-[#374151] border-[#E5E7EB] hover:bg-[#F8F9FC] rounded-md"
          >
            <Copy className="w-3 h-3" />
            Copiar
          </Button>
        </div>
      </div>

      {/* Document card — paper style */}
      <div className="flex-1 rounded-xl border border-[#E5E7EB] bg-[#FAFAFA] overflow-hidden shadow-sm relative min-h-[280px]">
        {/* Document header band */}
        <div className="bg-white border-b border-[#E5E7EB] px-5 py-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[10px] font-bold text-[#374151] tracking-[0.08em] uppercase leading-tight">
                {doc.titulo}
              </p>
              {doc.subtitulo.split('\n').map((line, i) => (
                <p key={i} className="text-[9px] text-[#6B7280] leading-tight mt-0.5">
                  {line}
                </p>
              ))}
            </div>
            <div className="flex-shrink-0 text-right">
              <span className="text-[8px] font-medium text-[#9CA3AF] uppercase tracking-wider">
                CERT. DIGITAL
              </span>
              <p className="text-[8px] text-[#9CA3AF]">ORIGINAL — PK/175</p>
            </div>
          </div>
        </div>

        {/* Document body */}
        <div className="px-5 py-4 relative">
          {ultimaMovimentacao && (
            <div className="mb-4 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2">
              <p className="text-[9px] font-semibold text-[#9CA3AF] uppercase tracking-wider mb-1">
                Ref. Movimentação
              </p>
              <p className="text-[10px] text-[#374151] leading-snug italic">
                &quot;{ultimaMovimentacao}&quot;
              </p>
            </div>
          )}

          <p
            className="text-[11px] text-[#374151] leading-relaxed whitespace-pre-line pr-16"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            {doc.conteudo}
          </p>

          {/* Digital seal */}
          <div className="absolute bottom-4 right-4 flex flex-col items-center">
            <div className="w-14 h-14 rounded-full border-2 border-[#8B5CF6]/30 flex items-center justify-center bg-[#8B5CF6]/5">
              <div className="text-center">
                <p className="text-[6px] font-bold text-[#8B5CF6] uppercase leading-tight">Assinatura</p>
                <p className="text-[6px] font-bold text-[#8B5CF6] uppercase leading-tight">Certificada</p>
              </div>
            </div>
          </div>
        </div>

        {/* Document footer */}
        <div className="px-5 py-2.5 border-t border-[#E5E7EB] bg-white flex items-center justify-between">
          <span className="text-[9px] text-[#9CA3AF]">{doc.origem}</span>
          <span className="text-[9px] text-[#9CA3AF]">{doc.paginas}</span>
        </div>
      </div>
    </div>
  )
}
