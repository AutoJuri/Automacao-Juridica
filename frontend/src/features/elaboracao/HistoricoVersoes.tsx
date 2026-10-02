import { Clock } from 'lucide-react'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import type { VersaoMinutaApi } from './elaboracao.types'

const ROTULO_ORIGEM: Record<VersaoMinutaApi['origem'], string> = {
  geracao: 'Geração inicial',
  chat: 'Edição via chat',
  grifo: 'Edição de trecho (grifo)',
}

interface HistoricoVersoesProps {
  versoes: VersaoMinutaApi[]
  versaoAtivaId: string | null
  carregando: boolean
  onRestaurar: (id: string) => void
}

export function HistoricoVersoes({
  versoes,
  versaoAtivaId,
  carregando,
  onRestaurar,
}: HistoricoVersoesProps) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Histórico de versões
      </p>
      <p className="text-[12px] text-[#6B7280] mb-2">
        Cada geração, chat ou edição de trecho pela IA salva uma versão no servidor.
      </p>

      {carregando ? (
        <p className="text-[12px] text-[#9CA3AF]">Carregando histórico…</p>
      ) : versoes.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF]">
          Nenhuma versão ainda — clique em Elaborar para gerar o primeiro rascunho.
        </p>
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
                title={ativa ? 'Versão atual' : `Voltar para ${ROTULO_ORIGEM[versao.origem]}`}
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
                    {ROTULO_ORIGEM[versao.origem]}
                    {ativa ? (
                      <span className="ml-1.5 text-[10px] font-medium text-[#2563EB]">Atual</span>
                    ) : null}
                  </p>
                  <p className="text-[11px] text-[#9CA3AF]">{formatarDataHoraSP(versao.criado_em)}</p>
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
