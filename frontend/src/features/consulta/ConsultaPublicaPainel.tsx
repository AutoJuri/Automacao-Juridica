import { formatarDataHoraSP, formatarDataSP } from '#/features/processos/processos.dates'
import { formatarNumeroCnj } from '#/features/processos/processos.format'

import type { ConsultaPublica, SituacaoConsultaPublica } from './consulta.publico'

const PLACEHOLDER = 'Não disponível'

const GRAU: Record<string, string> = {
  G1: '1º Grau',
  G2: '2º Grau',
  JE: 'Juizado especial',
  JEF: 'Juizado especial federal',
}

function rotuloGrauPublico(grau: string | null): string {
  if (!grau) {
    return PLACEHOLDER
  }
  return GRAU[grau] ?? grau
}

export function CardPublico({
  consulta,
  selecionado,
  onClick,
}: {
  consulta: ConsultaPublica
  selecionado: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'w-full text-left rounded-xl p-4 border bg-white transition-all cursor-pointer',
        selecionado
          ? 'border-[#2563EB] shadow-sm ring-1 ring-[#2563EB]/15'
          : 'border-[#FDE68A] hover:border-[#FCD34D] hover:bg-[#FFFBEB]',
      ].join(' ')}
    >
      <div className="flex items-center gap-1.5 mb-2">
        <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#FFFBEB] border border-[#FDE68A] text-[#92400E]">
          Dados públicos
        </span>
        <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#F3F4F6] border border-[#E5E7EB] text-[#374151]">
          {(consulta.tribunal ?? 'CNJ').toUpperCase()}
        </span>
      </div>
      <p className="font-mono text-[15px] font-bold text-[#111827]">
        {formatarNumeroCnj(consulta.numero)}
      </p>
      <p className="text-[13px] text-[#6B7280] mt-1.5">
        {consulta.classe_nome?.trim() || 'Classe não informada'}
      </p>
      <p className="text-[12px] text-[#92400E] mt-2">Não está na sua carteira</p>
    </button>
  )
}

export function FichaPublica({ consulta }: { consulta: ConsultaPublica }) {
  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-3">
        <span className="inline-flex px-2.5 py-0.5 rounded-md text-[12px] font-semibold text-[#92400E] bg-[#FFFBEB] border border-[#FDE68A]">
          Dados públicos · não está na sua carteira
        </span>
        <span className="inline-flex px-2.5 py-0.5 rounded-md text-[12px] font-semibold text-[#1E3A8A] bg-[#F3F4F6] border border-[#E5E7EB]">
          {(consulta.tribunal ?? 'CNJ').toUpperCase()}
        </span>
      </div>
      <p className="font-mono text-2xl font-bold text-[#111827] tracking-tight">
        {formatarNumeroCnj(consulta.numero)}
      </p>
      <p className="text-sm text-[#6B7280] mt-2 max-w-xl">
        Ficha da base nacional do CNJ. Nome das partes, advogado e documentos não vêm nessa
        consulta, e um processo novo pode levar alguns dias para aparecer.
      </p>

      <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-px rounded-xl border border-[#E5E7EB] bg-[#E5E7EB] overflow-hidden">
        <Bloco rotulo="Classe" valor={consulta.classe_nome} />
        <Bloco rotulo="Órgão julgador" valor={consulta.orgao_julgador} />
        <Bloco rotulo="Ajuizamento" valor={formatarDataHoraSP(consulta.data_ajuizamento)} />
        <Bloco rotulo="Grau" valor={rotuloGrauPublico(consulta.grau)} />
        {consulta.formato?.trim() ? <Bloco rotulo="Formato" valor={consulta.formato} /> : null}
        {consulta.sistema?.trim() ? <Bloco rotulo="Sistema" valor={consulta.sistema} /> : null}
        {consulta.atualizado_em ? (
          <Bloco rotulo="Atualizado no CNJ" valor={formatarDataHoraSP(consulta.atualizado_em)} />
        ) : null}
        {consulta.sigilo?.trim() ? <Bloco rotulo="Sigilo" valor={consulta.sigilo} /> : null}
      </div>
      <p className="text-[12px] text-[#9CA3AF] mt-2">Horários em Brasília.</p>

      {consulta.assuntos.length > 0 ? (
        <div className="mt-5">
          <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
            Assuntos
          </p>
          <ul className="flex flex-wrap gap-1.5">
            {consulta.assuntos.map((assunto, indice) => (
              <li
                key={`${assunto.codigo ?? 'assunto'}-${indice}`}
                className="inline-flex px-2.5 py-0.5 rounded-md text-[11px] font-medium text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]"
              >
                {assunto.nome?.trim() || PLACEHOLDER}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-6 pt-4 border-t border-[#E5E7EB]">
        <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-3">
          Movimentos públicos ({consulta.movimentos.length}
          {consulta.movimentos_total > consulta.movimentos.length
            ? ` de ${consulta.movimentos_total}`
            : ''}
          )
        </p>
        {consulta.movimentos_total > consulta.movimentos.length ? (
          <p className="text-[13px] text-[#6B7280] mb-3">
            Mostrando os {consulta.movimentos.length} mais recentes. O restante fica de fora
            desta ficha.
          </p>
        ) : null}
        {consulta.movimentos.length === 0 ? (
          <p className="text-sm text-[#9CA3AF]">Nenhum movimento público informado.</p>
        ) : (
          <ul className="space-y-2">
            {consulta.movimentos.map((movimento, indice) => (
              <li
                key={`${movimento.codigo ?? 'movimento'}-${indice}`}
                className="text-[13px] leading-snug"
              >
                <span className="text-[#9CA3AF] mr-2">{formatarDataSP(movimento.data_hora)}</span>
                <span className="text-[#111827]">{movimento.nome?.trim() || PLACEHOLDER}</span>
                {movimento.complementos.length > 0 ? (
                  <span className="block text-[#6B7280] mt-0.5">
                    {movimento.complementos.join(' · ')}
                  </span>
                ) : null}
                {movimento.orgao_julgador?.trim() &&
                movimento.orgao_julgador.trim() !== consulta.orgao_julgador?.trim() ? (
                  <span className="block text-[#9CA3AF] mt-0.5">{movimento.orgao_julgador}</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function Bloco({ rotulo, valor }: { rotulo: string; valor: string | null }) {
  const texto = valor?.trim() || PLACEHOLDER
  return (
    <div className="px-4 py-3 min-w-0 bg-white">
      <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
        {rotulo}
      </p>
      <p className="text-[13px] font-medium text-[#111827] leading-snug">{texto}</p>
    </div>
  )
}

/** Busca na base pública: três pontos, diferente do círculo de carregar a lista. */
export function EstadoBuscaPublica() {
  return (
    <div
      className="flex flex-1 min-h-[180px] w-full items-center justify-center px-6"
      role="status"
      aria-live="polite"
    >
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex items-end gap-1.5 h-4" aria-hidden>
          {[0, 150, 300].map((atraso) => (
            <span
              key={atraso}
              className="h-2 w-2 rounded-full bg-[#2563EB] animate-bounce"
              style={{ animationDelay: `${atraso}ms` }}
            />
          ))}
        </span>
        <p className="text-sm text-[#6B7280] max-w-[16rem]">Buscando dados públicos…</p>
      </div>
    </div>
  )
}

export function AvisoCentral({ mensagem, erro = false }: { mensagem: string; erro?: boolean }) {
  return (
    <div className="flex flex-1 min-h-[180px] w-full items-center justify-center px-6">
      <p
        className={[
          'text-sm text-center max-w-xs leading-relaxed',
          erro ? 'text-[#B91C1C]' : 'text-[#6B7280]',
        ].join(' ')}
      >
        {mensagem}
      </p>
    </div>
  )
}

export function avisoPublico(situacao: SituacaoConsultaPublica): string | null {
  if (situacao === 'ausente') {
    return 'Esse número não está na sua carteira e ainda não aparece nos dados públicos do CNJ.'
  }
  if (situacao === 'tribunal_nao_suportado') {
    return 'Esse tribunal ainda não entra na consulta pública.'
  }
  if (situacao === 'indisponivel') {
    return 'A consulta pública não respondeu. Tente de novo em instantes.'
  }
  return null
}
