import type { MovimentacoesStatus, PeticaoDiversaPublica } from './processos.types'
import { formatarDataSP } from './processos.dates'

interface PeticoesDiversasListaProps {
  peticoes: PeticaoDiversaPublica[]
  status: MovimentacoesStatus
}

function mensagemVazia(status: MovimentacoesStatus): string {
  if (status === 'pendente') {
    return 'Ainda não buscado no CPO'
  }
  if (status === 'indisponivel') {
    return 'Sem acesso a este bloco no e-SAJ (segredo de justiça ou sem vínculo pleno).'
  }
  return 'Nenhuma petição diversa coletada para este processo.'
}

export function PeticoesDiversasLista({ peticoes, status }: PeticoesDiversasListaProps) {
  return (
    <div className="mb-4">
      <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
        Petições diversas
      </p>
      {peticoes.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF] leading-relaxed">{mensagemVazia(status)}</p>
      ) : (
        <ul className="space-y-2">
          {peticoes.map((item) => (
            <li
              key={item.id}
              className="rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 py-2.5"
            >
              <p className="text-[12px] font-semibold text-[#111827] leading-snug whitespace-pre-wrap">
                {item.tipo.trim() || 'Petição'}
              </p>
              <p className="text-[11px] text-[#6B7280] tabular-nums mt-0.5 whitespace-pre-wrap">
                {formatarDataSP(item.data_peticao)}
                {item.protocolo?.trim() ? ` · ${item.protocolo.trim()}` : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
