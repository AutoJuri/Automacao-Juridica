import { Clock, Save } from 'lucide-react'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import type { VersaoMinuta } from './elaboracao.versoes'

interface HistoricoVersoesProps {
  versoes: VersaoMinuta[]
  versaoAtivaId: string | null
  onSalvar: () => void
  onRestaurar: (id: string) => void
}

export function HistoricoVersoes({
  versoes,
  versaoAtivaId,
  onSalvar,
  onRestaurar,
}: HistoricoVersoesProps) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Histórico de versões
      </p>
      <p className="text-[12px] text-[#6B7280] mb-2">
        Salva a minuta neste browser. Não vai ao servidor — se limpar os dados do site, some.
      </p>

      <button
        type="button"
        onClick={onSalvar}
        className="w-full h-9 mb-3 inline-flex items-center justify-center gap-1.5 rounded-lg bg-[#2563EB] text-[12px] font-semibold text-white hover:bg-[#1D4ED8]"
      >
        <Save className="w-3.5 h-3.5" aria-hidden />
        Salvar versão
      </button>

      {versoes.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF]">Nenhuma versão salva ainda.</p>
      ) : (
        <div className="space-y-1">
          {versoes.map((versao) => {
            const ativa = versao.id === versaoAtivaId
            return (
              <button
                key={versao.id}
                type="button"
                onClick={() => {
                  if (!ativa) {
                    onRestaurar(versao.id)
                  }
                }}
                disabled={ativa}
                title={ativa ? 'Versão atual' : `Voltar para ${versao.rotulo}`}
                className={`w-full text-left flex items-center gap-2.5 px-2.5 py-2 rounded-lg border transition-colors ${
                  ativa
                    ? 'bg-[#EFF6FF] border-[#2563EB] text-[#1D4ED8] cursor-default'
                    : 'bg-white border-[#E5E7EB] text-[#374151] hover:border-[#2563EB] hover:bg-[#EFF6FF] cursor-pointer'
                }`}
              >
                <Clock
                  className={`w-3.5 h-3.5 shrink-0 ${ativa ? 'text-[#2563EB]' : 'text-[#9CA3AF]'}`}
                />
                <div className="flex-1 min-w-0">
                  <p className={`text-[13px] font-semibold ${ativa ? 'text-[#1D4ED8]' : 'text-[#374151]'}`}>
                    {versao.rotulo}
                    {ativa ? (
                      <span className="ml-1.5 text-[10px] font-medium text-[#2563EB]">Atual</span>
                    ) : null}
                  </p>
                  <p className="text-[11px] text-[#9CA3AF]">{formatarDataHoraSP(versao.criadoEm)}</p>
                </div>
                {ativa ? null : (
                  <span className="text-[11px] font-semibold text-[#2563EB] shrink-0">Voltar</span>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
