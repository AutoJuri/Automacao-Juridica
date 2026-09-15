import { useState } from 'react'
import { CheckCircle2, ChevronRight, Circle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '#/components/ui/dialog'
import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { completudeDadosProcesso } from './elaboracao.processo'

interface MedidorCompletudeProps {
  processo: ProcessoDetalhe | null
}

export function MedidorCompletude({ processo }: MedidorCompletudeProps) {
  const [open, setOpen] = useState(false)
  const resultado = processo ? completudeDadosProcesso(processo) : null
  const percentual = resultado?.percentual ?? 0
  const raio = 15.9155
  const circunferencia = 2 * Math.PI * raio
  const preenchido = (percentual / 100) * circunferencia

  return (
    <div>
        <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-3">
        Qualidade processual
      </p>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <button type="button" className="w-full text-left group rounded-xl bg-gradient-to-br from-[#1D4ED8] to-[#2563EB] p-4 text-white">
            <div className="flex items-center gap-3">
              <svg viewBox="0 0 36 36" className="w-14 h-14 shrink-0" aria-hidden>
                <circle
                  cx="18"
                  cy="18"
                  r={raio}
                  fill="none"
                  stroke="rgba(255,255,255,0.25)"
                  strokeWidth="3"
                />
                <circle
                  cx="18"
                  cy="18"
                  r={raio}
                  fill="none"
                  stroke="#BBF7D0"
                  strokeWidth="3"
                  strokeDasharray={`${preenchido} ${circunferencia}`}
                  strokeLinecap="round"
                  transform="rotate(-90 18 18)"
                />
                <text
                  x="18"
                  y="19.5"
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="8"
                  fontWeight="700"
                >
                  {resultado ? `${percentual}%` : '—'}
                </text>
              </svg>
              <div className="min-w-0">
                <p className="text-[14px] font-semibold">Completude: {resultado ? `${percentual}%` : '—'}</p>
                <p className="text-[12px] text-white/80 mt-0.5">
                  {resultado
                    ? percentual >= 80
                      ? 'Peça bem fundamentada nos dados coletados'
                      : `${resultado.atendidos}/${resultado.total} campos do e-SAJ`
                    : 'Aguardando processo'}
                </p>
                <p className="inline-flex items-center gap-0.5 text-[12px] font-semibold text-white mt-1 group-hover:underline">
                  Expandir requisitos
                  <ChevronRight className="w-3 h-3" />
                </p>
              </div>
            </div>
          </button>
        </DialogTrigger>

        <DialogContent className="max-w-sm bg-white border border-[#E5E7EB] shadow-xl">
          <DialogHeader>
            <DialogTitle className="text-[14px] font-semibold text-[#111827]">
              Dados disponíveis para a minuta
            </DialogTitle>
          </DialogHeader>
          <p className="text-[12px] text-[#6B7280]">
            Mede o que o ciclo já coletou — não a qualidade de uma peça gerada.
          </p>
          <div className="mt-2 space-y-1.5">
            {(resultado?.itens ?? []).map((item) => (
              <div key={item.id} className="flex items-center gap-2.5 py-1.5 px-2 rounded-md">
                {item.preenchido ? (
                  <CheckCircle2 className="w-4 h-4 text-[#2563EB] shrink-0" />
                ) : (
                  <Circle className="w-4 h-4 text-[#D1D5DB] shrink-0" />
                )}
                <span
                  className={`text-[12px] ${item.preenchido ? 'text-[#374151]' : 'text-[#9CA3AF]'}`}
                >
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
