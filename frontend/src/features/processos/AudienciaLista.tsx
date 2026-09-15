import type { AudienciaPublica } from './processos.types'
import { formatarDataHoraSP } from './processos.dates'

interface AudienciaListaProps {
  audiencias: AudienciaPublica[]
}

export function AudienciaLista({ audiencias }: AudienciaListaProps) {
  return (
    <div className="mb-4">
      <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
        Audiências
      </p>
      {audiencias.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF] leading-relaxed">
          Nenhuma audiência coletada para este processo.
        </p>
      ) : (
        <ul className="space-y-2">
          {audiencias.map((item) => (
            <li
              key={item.id}
              className="rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 py-2.5"
            >
              <p className="text-[12px] font-semibold text-[#111827] leading-snug">
                {item.titulo?.trim() || 'Audiência'}
              </p>
              <p className="text-[11px] text-[#6B7280] tabular-nums mt-0.5">
                {formatarDataHoraSP(item.data_audiencia)}
                {item.local ? ` · ${item.local}` : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
