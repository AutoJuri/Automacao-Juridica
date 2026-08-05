import { useState } from 'react'
import { CheckCircle2, XCircle, ChevronRight } from 'lucide-react'
import { Progress } from '#/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '#/components/ui/dialog'
import { requisitosCompletude, PERCENTUAL_COMPLETUDE } from './elaboracao.mock'

export function MedidorCompletude() {
  const [open, setOpen] = useState(false)

  const atendidos = requisitosCompletude.filter((r) => r.atendido).length
  const total = requisitosCompletude.length

  const cor =
    PERCENTUAL_COMPLETUDE >= 80
      ? 'text-[#22C55E]'
      : PERCENTUAL_COMPLETUDE >= 50
        ? 'text-[#F59E0B]'
        : 'text-[#EF4444]'

  const corBarra =
    PERCENTUAL_COMPLETUDE >= 80
      ? '[&>div]:bg-[#22C55E]'
      : PERCENTUAL_COMPLETUDE >= 50
        ? '[&>div]:bg-[#F59E0B]'
        : '[&>div]:bg-[#EF4444]'

  return (
    <div>
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Completude da Peça
      </p>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <button className="w-full text-left group">
            <div className="flex items-center justify-between mb-1.5">
              <span className={`text-2xl font-bold ${cor}`}>
                {PERCENTUAL_COMPLETUDE}%
              </span>
              <div className="flex items-center gap-1 text-[10px] text-[#9CA3AF] group-hover:text-[#374151] transition-colors">
                <span>{atendidos}/{total} itens</span>
                <ChevronRight className="w-3 h-3" />
              </div>
            </div>
            <Progress
              value={PERCENTUAL_COMPLETUDE}
              className={`h-2 bg-[#F3F4F6] ${corBarra}`}
            />
            <p className="text-[10px] text-[#9CA3AF] mt-1.5 group-hover:text-[#374151] transition-colors">
              Clique para ver os requisitos
            </p>
          </button>
        </DialogTrigger>

        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-[14px] font-semibold text-[#111827]">
              Requisitos da Peça
            </DialogTitle>
          </DialogHeader>

          <div className="mt-2 space-y-1.5">
            {requisitosCompletude.map((req) => (
              <div
                key={req.id}
                className="flex items-center gap-2.5 py-1.5 px-2 rounded-md hover:bg-[#F9FAFB]"
              >
                {req.atendido ? (
                  <CheckCircle2 className="w-4 h-4 text-[#22C55E] shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-[#D1D5DB] shrink-0" />
                )}
                <span
                  className={`text-[12px] ${req.atendido ? 'text-[#374151]' : 'text-[#9CA3AF]'}`}
                >
                  {req.descricao}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-[#E5E7EB]">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#6B7280]">Pontuação geral</span>
              <span className={`font-bold text-[14px] ${cor}`}>
                {PERCENTUAL_COMPLETUDE}%
              </span>
            </div>
            <Progress
              value={PERCENTUAL_COMPLETUDE}
              className={`h-2 mt-2 bg-[#F3F4F6] ${corBarra}`}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
