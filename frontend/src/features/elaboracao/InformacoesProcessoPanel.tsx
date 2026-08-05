import { Separator } from '#/components/ui/separator'
import { processosMockados, movimentacoesMockadas } from '#/features/processos/processos.mock'

interface InformacoesProcessoPanelProps {
  processoId: number
}

export function InformacoesProcessoPanel({ processoId }: InformacoesProcessoPanelProps) {
  const processo = processosMockados.find((p) => p.id === processoId)
  const movimentacoes = movimentacoesMockadas
    .filter((m) => m.processoId === processoId)
    .slice(0, 3)

  if (!processo) return null

  return (
    <div>
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-3">
        Informações do Processo
      </p>

      <div className="space-y-2.5">
        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-0.5">Número</p>
          <p className="font-mono text-[11px] font-semibold text-[#111827] leading-tight">
            {processo.numero}
          </p>
        </div>

        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-0.5">Autor</p>
          <p className="text-[12px] font-medium text-[#111827]">{processo.cliente}</p>
        </div>

        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-0.5">Réu</p>
          <p className="text-[12px] font-medium text-[#111827]">Banco Meridional S.A.</p>
        </div>

        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-0.5">Tribunal</p>
          <p className="text-[12px] font-medium text-[#111827]">{processo.tribunal}</p>
        </div>

        <div>
          <p className="text-[9px] text-[#9CA3AF] uppercase tracking-widest mb-0.5">Magistrado</p>
          <p className="text-[12px] font-medium text-[#111827] leading-snug">{processo.magistrado}</p>
        </div>
      </div>

      <Separator className="my-3 bg-border-active" />

      <div>
        <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
          Andamentos Recentes
        </p>
        <div className="space-y-2">
          {movimentacoes.map((mov) => (
            <div key={mov.id} className="flex gap-2">
              <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#3B5BDB] shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] font-semibold text-[#374151] leading-snug">{mov.nomeEtapa}</p>
                <p className="text-[10px] text-[#9CA3AF]">{mov.data}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
