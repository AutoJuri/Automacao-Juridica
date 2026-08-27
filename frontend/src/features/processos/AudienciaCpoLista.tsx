import type { AudienciaCpoPublica, MovimentacoesStatus } from './processos.types'
import { formatarDataSP } from './processos.dates'

interface AudienciaCpoListaProps {
  audiencias: AudienciaCpoPublica[]
  status: MovimentacoesStatus
}

function mensagemVazia(status: MovimentacoesStatus): string {
  if (status === 'pendente') {
    return 'Ainda não buscado no CPO'
  }
  if (status === 'indisponivel') {
    return 'Sem acesso a este bloco no e-SAJ (segredo de justiça ou sem vínculo pleno).'
  }
  return 'Não há audiências neste processo no e-SAJ.'
}

export function AudienciaCpoLista({ audiencias, status }: AudienciaCpoListaProps) {
  return (
    <div className="mb-4">
      <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
        Audiências no e-SAJ (CPO)
      </p>
      {audiencias.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF] leading-relaxed">{mensagemVazia(status)}</p>
      ) : (
        <ul className="space-y-2">
          {audiencias.map((item) => (
            <li
              key={item.id}
              className="rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 py-2.5"
            >
              <p className="text-[12px] font-semibold text-[#111827] leading-snug whitespace-pre-wrap">
                {item.titulo.trim() || 'Audiência'}
              </p>
              <p className="text-[11px] text-[#6B7280] tabular-nums mt-0.5 whitespace-pre-wrap">
                {formatarDataSP(item.data_audiencia)}
                {item.situacao?.trim() ? ` · ${item.situacao.trim()}` : ''}
                {item.qt_pessoas?.trim() ? ` · ${item.qt_pessoas.trim()} pessoa(s)` : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
