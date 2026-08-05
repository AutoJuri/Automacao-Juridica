import { Clock, RotateCcw } from 'lucide-react'
import { versoesMock } from './elaboracao.mock'

export function HistoricoVersoes() {
  return (
    <div>
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Histórico de Versões
      </p>

      <div className="space-y-1">
        {versoesMock.map((versao) => (
          <div
            key={versao.id}
            className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg border cursor-pointer transition-colors group ${
              versao.ativa
                ? 'bg-[#EEF2FF] border-[#3B5BDB]/30 text-[#3B5BDB]'
                : 'bg-white border-border-active hover:bg-surface-hover text-[#374151]'
            }`}
          >
            <Clock className={`w-3.5 h-3.5 shrink-0 ${versao.ativa ? 'text-[#3B5BDB]' : 'text-[#9CA3AF]'}`} />
            <div className="flex-1 min-w-0">
              <p className={`text-[11px] font-semibold ${versao.ativa ? 'text-[#3B5BDB]' : 'text-[#374151]'}`}>
                {versao.rotulo}
                {versao.ativa && (
                  <span className="ml-1.5 text-[9px] font-medium text-[#3B5BDB] bg-[#EEF2FF] px-1.5 py-0.5 rounded-full border border-[#3B5BDB]/20">
                    Atual
                  </span>
                )}
              </p>
              <p className="text-[10px] text-[#9CA3AF]">{versao.horario}</p>
            </div>
            {!versao.ativa && (
              <RotateCcw className="w-3 h-3 text-[#D1D5DB] group-hover:text-[#9CA3AF] shrink-0 transition-colors" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
