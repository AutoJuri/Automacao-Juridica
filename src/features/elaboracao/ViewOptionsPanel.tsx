import { UploadCloud, FileText } from 'lucide-react'
import { Switch } from '#/components/ui/switch'
import { Label } from '#/components/ui/label'
import { Button } from '#/components/ui/button'

interface ViewOptionsPanelProps {
  highlightAtivo: boolean
  onToggleHighlight: (v: boolean) => void
}

export function ViewOptionsPanel({ highlightAtivo, onToggleHighlight }: ViewOptionsPanelProps) {
  return (
    <div className="space-y-4">
      {/* Upload tese/jurisprudência */}
      <div>
        <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
          Tese / Jurisprudência
        </p>
        <div className="border-2 border-dashed border-border-active rounded-lg p-3 flex flex-col items-center gap-2 bg-white/70 hover:bg-white transition-colors cursor-default">
          <UploadCloud className="w-6 h-6 text-[#9CA3AF]" />
          <p className="text-[10px] text-[#6B7280] text-center leading-snug">
            Upload de tese específica
          </p>
          <Button
            variant="outline"
            size="sm"
            className="h-6 px-2.5 text-[10px] gap-1 border-[#E5E7EB] text-[#374151] hover:bg-white"
          >
            <FileText className="w-3 h-3" />
            Selecionar
          </Button>
        </div>

        <div className="mt-2 flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-[#E5E7EB] bg-white">
          <div className="w-5 h-5 rounded flex items-center justify-center bg-[#FEF9C3]">
            <FileText className="w-3 h-3 text-[#92400E]" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-medium text-[#111827] truncate">tese_propriedade.pdf</p>
            <p className="text-[9px] text-[#9CA3AF]">Carregado • 120 KB</p>
          </div>
        </div>
      </div>

      {/* Toggle highlight */}
      <div>
        <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
          Visualização
        </p>
        <div className="flex items-center justify-between gap-2 px-2.5 py-2 rounded-lg border border-[#E5E7EB] bg-white">
          <Label htmlFor="toggle-highlight" className="cursor-pointer flex-1">
            <span className="text-[11px] font-medium text-[#374151] block">
              Modo highlight
            </span>
            <span className="text-[10px] text-[#9CA3AF]">
              Ícones de jurisprudência na peça
            </span>
          </Label>
          <Switch
            id="toggle-highlight"
            checked={highlightAtivo}
            onCheckedChange={onToggleHighlight}
          />
        </div>
      </div>
    </div>
  )
}
