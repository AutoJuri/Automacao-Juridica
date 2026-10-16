import { useState } from 'react'
import { FileText, Trash2 } from 'lucide-react'

import { formatarNumeroCnj } from '#/features/processos/processos.format'

import { atualizadaHa } from './elaboracao.tempo'
import type { ElaboracaoCard as Elaboracao } from './elaboracoes.types'

interface ElaboracaoCardProps {
  elaboracao: Elaboracao
  excluindo: boolean
  onAbrir: (id: string) => void
  onExcluir: (id: string) => void
}

export function ElaboracaoCard({
  elaboracao,
  excluindo,
  onAbrir,
  onExcluir,
}: ElaboracaoCardProps) {
  const [confirmar, setConfirmar] = useState(false)
  const numero = elaboracao.tem_processo
    ? formatarNumeroCnj(elaboracao.nu_processo)
    : elaboracao.nu_processo?.trim()
      ? formatarNumeroCnj(elaboracao.nu_processo)
      : 'Sem processo'
  const titulo = elaboracao.tem_processo ? elaboracao.rotulo : elaboracao.titulo || elaboracao.rotulo
  const polos = [elaboracao.autor, elaboracao.reu].filter(Boolean).join(' × ')

  return (
    <article className="flex flex-col rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition duration-150 hover:-translate-y-0.5 hover:border-[#93C5FD] hover:shadow-md">
      <button
        type="button"
        onClick={() => onAbrir(elaboracao.id)}
        className="min-w-0 flex-1 text-left"
      >
        <p className="text-[11px] font-semibold tracking-[0.14em] text-[#2563EB] uppercase">
          {elaboracao.rotulo}
        </p>
        <h3 className="mt-1 truncate text-[15px] font-semibold text-[#111827]">{titulo}</h3>
        <p className="mt-1 flex items-center gap-1.5 text-[13px] text-[#6B7280]">
          <FileText className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="truncate">{numero}</span>
        </p>
        {polos ? <p className="mt-2 truncate text-[13px] text-[#374151]">{polos}</p> : null}
        <p className="mt-3 text-[12px] text-[#9CA3AF]">{atualizadaHa(elaboracao.updated_at)}</p>
      </button>
      <div className="mt-3 flex justify-end">
        <button
          type="button"
          disabled={excluindo}
          aria-label={confirmar ? `Confirmar exclusão de ${titulo}` : `Excluir ${titulo}`}
          onClick={() => {
            if (!confirmar) {
              setConfirmar(true)
              return
            }
            onExcluir(elaboracao.id)
          }}
          className={[
            'inline-flex h-7 items-center justify-center rounded-md transition-colors',
            confirmar
              ? 'bg-[#FEF2F2] px-1.5 text-[11px] font-semibold text-[#B91C1C] hover:bg-[#FEE2E2]'
              : 'w-7 text-[#9CA3AF] hover:bg-[#FEF2F2] hover:text-[#B91C1C]',
          ].join(' ')}
        >
          {confirmar ? 'Excluir?' : <Trash2 className="h-3.5 w-3.5" aria-hidden />}
        </button>
      </div>
    </article>
  )
}
