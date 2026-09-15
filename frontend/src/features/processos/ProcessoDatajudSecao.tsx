import { formatarDataHoraSP, formatarDataSP } from './processos.dates'
import type { ProcessoDatajudPublica } from './processos.types'

const PLACEHOLDER = 'Não disponível'

interface ProcessoDatajudSecaoProps {
  datajud: ProcessoDatajudPublica | null
}

/**
 * Seção somente-leitura do complemento público do DataJud (CNJ) —
 * Etapa 9 / ADR-015. Nunca sobrescreve o que já vem do e-SAJ (classe,
 * assunto, foro, vara…) — é sempre um bloco separado, claramente rotulado
 * como fonte pública e complementar.
 */
export function ProcessoDatajudSecao({ datajud }: ProcessoDatajudSecaoProps) {
  if (!datajud || !datajud.encontrado) {
    return (
      <p className="text-[12px] text-[#9CA3AF] italic leading-relaxed">
        Sem dados públicos do DataJud ainda — o complemento roda uma vez por dia e pode levar
        alguns dias para aparecer.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
        Dados públicos da base nacional do CNJ, complementares aos coletados no e-SAJ — podem
        estar com alguns dias de defasagem.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-4">
        <div className="min-w-0">
          <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1.5">
            Classe (DataJud)
          </p>
          <p className="text-[13px] font-medium text-[#111827] leading-snug">
            {datajud.classe_nome?.trim() || PLACEHOLDER}
          </p>
        </div>
        <div className="min-w-0">
          <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1.5">
            Órgão julgador (DataJud)
          </p>
          <p className="text-[13px] font-medium text-[#111827] leading-snug">
            {datajud.orgao_julgador?.trim() || PLACEHOLDER}
          </p>
        </div>
        <div className="min-w-0">
          <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1.5">
            Data de ajuizamento (DataJud)
          </p>
          <p className="text-[13px] font-medium text-[#111827] leading-snug">
            {formatarDataSP(datajud.data_ajuizamento)}
          </p>
        </div>
        <div className="min-w-0">
          <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1.5">
            Última consulta ao DataJud
          </p>
          <p className="text-[13px] font-medium text-[#111827] leading-snug">
            {formatarDataHoraSP(datajud.ultima_consulta_em)}
          </p>
        </div>
      </div>

      {datajud.assuntos.length > 0 ? (
        <div>
          <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
            Assuntos (DataJud)
          </p>
          <ul className="flex flex-wrap gap-1.5">
            {datajud.assuntos.map((assunto, indice) => (
              <li
                key={`${assunto.codigo ?? 'assunto'}-${indice}`}
                className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-medium text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]"
              >
                {assunto.nome?.trim() || PLACEHOLDER}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {datajud.movimentos.length > 0 ? (
        <div>
          <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
            Movimentos públicos (DataJud)
          </p>
          <ul className="space-y-2">
            {datajud.movimentos.map((movimento, indice) => (
              <li key={`${movimento.codigo ?? 'movimento'}-${indice}`} className="text-[13px] leading-snug">
                <span className="text-[#9CA3AF] mr-2">{formatarDataSP(movimento.data_hora)}</span>
                <span className="text-[#111827]">{movimento.nome?.trim() || PLACEHOLDER}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
