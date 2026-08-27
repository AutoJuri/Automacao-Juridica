import { useState } from 'react'
import { ExternalLink, FileText } from 'lucide-react'
import type { MovimentacaoPublica, MovimentacoesStatus } from './processos.types'
import { formatarDataSP } from './processos.dates'
import { hrefDocumentoMovimentacao } from './processos.urls'

interface MovimentacoesTimelineProps {
  movimentacoes: MovimentacaoPublica[]
  status?: MovimentacoesStatus
  urlCpo?: string | null
}

const MENSAGEM_VAZIA: Record<MovimentacoesStatus, string> = {
  ok: 'Nenhuma movimentação coletada para este processo.',
  pendente:
    'As movimentações deste processo ainda não foram buscadas no e-SAJ. Elas entram no próximo ciclo de coleta.',
  indisponivel:
    'Sem acesso às movimentações deste processo no e-SAJ (segredo de justiça ou sem vínculo pleno). Não solicitamos senha dos autos.',
}

export function MovimentacoesTimeline({
  movimentacoes,
  status = 'pendente',
  urlCpo = null,
}: MovimentacoesTimelineProps) {
  const [selecionadoId, setSelecionadoId] = useState<string | null>(movimentacoes[0]?.id ?? null)

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
          Movimentações
        </p>
        <p className="text-[11px] text-[#9CA3AF] mt-1">
          Andamentos coletados do CPO (e-SAJ) para este processo
        </p>
      </div>

      {movimentacoes.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF] leading-relaxed">{MENSAGEM_VAZIA[status]}</p>
      ) : (
        <div className="space-y-3">
          {movimentacoes.map((item) => {
            const isSelected = item.id === selecionadoId
            const detalhe = item.descricao.trim()
            const hrefDocumento = hrefDocumentoMovimentacao(
              item.tem_documento,
              item.url_documento,
              urlCpo,
            )
            return (
              <article
                key={item.id}
                onClick={() => setSelecionadoId(item.id)}
                className={[
                  'w-full text-left rounded-xl px-4 py-3.5 border transition-all duration-150 cursor-pointer',
                  isSelected
                    ? 'border-[#8B5CF6] bg-[#FAF5FF] shadow-sm'
                    : 'border-[#E5E7EB] bg-white hover:border-[#C7D0E8] hover:bg-[#F8F9FC]',
                ].join(' ')}
              >
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className="text-[11px] font-medium text-[#6B7280] tabular-nums">
                    {formatarDataSP(item.data_movimentacao)}
                  </span>
                  {item.tem_documento ? (
                    <span
                      className="inline-flex items-center text-[#6B7280]"
                      title="Há documento no e-SAJ"
                      aria-label="Há documento no e-SAJ"
                    >
                      <FileText className="w-3.5 h-3.5" aria-hidden />
                    </span>
                  ) : null}
                </div>
                <p className="text-[12px] font-semibold text-[#111827] leading-snug">
                  {item.titulo?.trim() || 'Movimentação'}
                </p>
                {detalhe ? (
                  <p className="text-[12px] text-[#374151] leading-relaxed whitespace-pre-wrap mt-1">
                    {detalhe}
                  </p>
                ) : null}
                {item.tem_documento ? (
                  hrefDocumento ? (
                    <a
                      href={hrefDocumento}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(evento) => evento.stopPropagation()}
                      className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-medium text-[#3B5BDB] hover:underline"
                    >
                      <ExternalLink className="w-3.5 h-3.5" aria-hidden />
                      Abrir documento no e-SAJ
                    </a>
                  ) : (
                    <p className="mt-2 text-[11px] text-[#6B7280]">Há documento no e-SAJ</p>
                  )
                ) : null}
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
