import {
  Scissors,
  Copy,
  Download,
  FileText,
  HardDrive,
  Pencil,
  CheckCheck,
} from 'lucide-react'
import { Button } from '#/components/ui/button'

interface DocumentToolbarProps {
  editando: boolean
  onToggleEditar: () => void
}

export function DocumentToolbar({ editando, onToggleEditar }: DocumentToolbarProps) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2.5 text-[11px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
      >
        <Scissors className="w-3.5 h-3.5" />
        Extrair
      </Button>

      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2.5 text-[11px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
      >
        <Copy className="w-3.5 h-3.5" />
        Copiar
      </Button>

      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2.5 text-[11px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
      >
        <Download className="w-3.5 h-3.5" />
        Baixar PDF
      </Button>

      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2.5 text-[11px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
      >
        <FileText className="w-3.5 h-3.5" />
        Exportar Word
      </Button>

      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2.5 text-[11px] gap-1.5 text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
      >
        <HardDrive className="w-3.5 h-3.5" />
        Drive
      </Button>

      <div className="flex-1" />

      <Button
        size="sm"
        onClick={onToggleEditar}
        className={
          editando
            ? 'h-8 px-4 text-[11px] font-semibold gap-1.5 bg-[#22C55E] hover:bg-[#16A34A] text-white'
            : 'h-8 px-4 text-[11px] font-semibold gap-1.5 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white'
        }
      >
        {editando ? (
          <>
            <CheckCheck className="w-3.5 h-3.5" />
            Salvar
          </>
        ) : (
          <>
            <Pencil className="w-3.5 h-3.5" />
            Editar
          </>
        )}
      </Button>
    </div>
  )
}
