import { useState } from 'react'
import { FileText, Folder, Pencil, Trash2 } from 'lucide-react'

import { formatarNumeroCnj } from '#/features/processos/processos.format'

import { atualizadaHa } from '#/features/elaboracao/elaboracao.tempo'

import { rotuloArquivos } from './drive.format'
import type { Pasta } from './drive.types'

interface PastaCardProps {
  pasta: Pasta
  excluindo: boolean
  onAbrir: (id: string) => void
  onEditar: (pasta: Pasta) => void
  onExcluir: (id: string) => void
}

export function PastaCard({ pasta, excluindo, onAbrir, onEditar, onExcluir }: PastaCardProps) {
  const [confirmar, setConfirmar] = useState(false)
  const processo = pasta.processo
  const polos = processo ? [processo.autor, processo.reu].filter(Boolean).join(' × ') : ''

  return (
    <article className="flex flex-col rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition duration-150 hover:-translate-y-0.5 hover:border-[#93C5FD] hover:shadow-md">
      <button type="button" onClick={() => onAbrir(pasta.id)} className="min-w-0 flex-1 text-left">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB]">
          <Folder className="h-5 w-5" aria-hidden />
        </span>
        <h3 className="mt-3 truncate text-[15px] font-semibold text-[#111827]">{pasta.nome}</h3>
        <p className="mt-1 flex items-center gap-1.5 text-[13px] text-[#6B7280]">
          <FileText className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="truncate">
            {processo ? formatarNumeroCnj(processo.nu_processo) : 'Sem processo'}
          </span>
        </p>
        {polos ? <p className="mt-2 truncate text-[13px] text-[#374151]">{polos}</p> : null}
        <p className="mt-3 text-[12px] text-[#9CA3AF]">
          {rotuloArquivos(pasta.total_arquivos)} · {atualizadaHa(pasta.updated_at)}
        </p>
      </button>
      <div className="mt-3 flex justify-end gap-1">
        <button
          type="button"
          aria-label={`Editar ${pasta.nome}`}
          onClick={() => onEditar(pasta)}
          className="inline-flex h-7 w-7 items-center justify-center rounded-md text-[#9CA3AF] transition-colors hover:bg-[#EFF6FF] hover:text-[#2563EB]"
        >
          <Pencil className="h-3.5 w-3.5" aria-hidden />
        </button>
        <button
          type="button"
          disabled={excluindo}
          aria-label={confirmar ? `Confirmar exclusão de ${pasta.nome}` : `Excluir ${pasta.nome}`}
          onBlur={() => setConfirmar(false)}
          onClick={() => {
            if (!confirmar) {
              setConfirmar(true)
              return
            }
            onExcluir(pasta.id)
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
