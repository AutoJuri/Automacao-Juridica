import { UploadCloud, FileUp } from 'lucide-react'
import { Button } from '#/components/ui/button'

export function SeletorPecaEspecifica() {
  return (
    <div>
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Peça Modelo Específica
      </p>
      <p className="text-[10px] text-[#9CA3AF] leading-snug mb-3">
        Envie uma peça modelo de tese, formatação ou jurisprudência. A IA irá adaptá-la ao contexto do caso atual.
      </p>

      <div className="border-2 border-dashed border-border-active rounded-lg p-4 flex flex-col items-center gap-2 bg-white/70 hover:bg-white transition-colors cursor-default">
        <UploadCloud className="w-8 h-8 text-[#9CA3AF]" />
        <p className="text-[11px] font-medium text-[#6B7280] text-center">
          Arraste um arquivo aqui
        </p>
        <p className="text-[10px] text-[#9CA3AF]">PDF, DOCX ou TXT</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-1 h-7 px-3 text-[11px] gap-1.5 border-[#E5E7EB] text-[#374151] hover:bg-white"
        >
          <FileUp className="w-3 h-3" />
          Selecionar arquivo
        </Button>
      </div>

      <div className="mt-2 flex items-center gap-2 px-3 py-2 rounded-md border border-[#E5E7EB] bg-white">
        <div className="w-6 h-6 rounded flex items-center justify-center bg-[#EEF2FF]">
          <FileUp className="w-3.5 h-3.5 text-[#3B5BDB]" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium text-[#111827] truncate">modelo_contestacao_v2.docx</p>
          <p className="text-[10px] text-[#9CA3AF]">Carregado • 48 KB</p>
        </div>
      </div>
    </div>
  )
}
