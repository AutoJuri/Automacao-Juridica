import { formatarNumeroCnj, rotuloTribunal } from '#/features/processos/processos.format'

import type { ProcessoParaIniciar } from './elaboracoes.types'

interface ProcessoParaIniciarCardProps {
  processo: ProcessoParaIniciar
  onComecar: (processo: ProcessoParaIniciar) => void
}

export function ProcessoParaIniciarCard({ processo, onComecar }: ProcessoParaIniciarCardProps) {
  const polos = [processo.autor, processo.reu].filter(Boolean).join(' × ')
  return (
    <article className="flex flex-col rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition duration-150 hover:-translate-y-0.5 hover:border-[#93C5FD] hover:shadow-md">
      <p className="text-[11px] font-semibold tracking-[0.14em] text-[#6B7280] uppercase">
        {rotuloTribunal(processo.tribunal)}
      </p>
      <h3 className="mt-1 truncate text-[15px] font-semibold text-[#111827]">
        {formatarNumeroCnj(processo.nu_processo)}
      </h3>
      {processo.classe ? (
        <p className="mt-1 truncate text-[13px] text-[#6B7280]">{processo.classe}</p>
      ) : null}
      {polos ? <p className="mt-2 truncate text-[13px] text-[#374151]">{polos}</p> : null}
      <div className="mt-4">
        <button
          type="button"
          onClick={() => onComecar(processo)}
          className="h-9 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white transition-colors hover:bg-[#1D4ED8] active:bg-[#1E40AF]"
        >
          Começar
        </button>
      </div>
    </article>
  )
}
