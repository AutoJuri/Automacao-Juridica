import { Download, Pin } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { Button } from '#/components/ui/button'
import { Separator } from '#/components/ui/separator'
import { MovimentacaoTimeline } from './MovimentacaoTimeline'
import { GabineteDocumentos } from './GabineteDocumentos'
import {
  processosMockados,
  movimentacoesMockadas,
  documentosMockados,
} from './processos.mock'

interface ProcessoDetalheProps {
  processoId: number
}

export function ProcessoDetalhe({ processoId }: ProcessoDetalheProps) {
  const navigate = useNavigate()
  const processo = processosMockados.find((p) => p.id === processoId)
  const movimentacoes = movimentacoesMockadas.filter((m) => m.processoId === processoId)
  const documentos = documentosMockados.filter((d) => d.processoId === processoId)

  if (!processo) {
    return (
      <div className="flex-1 flex items-center justify-center rounded-xl border border-[#E5E7EB] bg-white min-h-[200px]">
        <p className="text-[#9CA3AF] text-sm">
          Nenhum processo selecionado ou nenhum resultado para os filtros aplicados.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden rounded-xl border border-[#E5E7EB] bg-white shadow-sm min-h-0">
      <div className="flex-1 flex flex-col overflow-hidden px-6 pt-5 pb-5">
        {/* Top row — badges + action */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center flex-wrap gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-semibold text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
              {processo.tribunal}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] font-semibold tracking-wide text-[#6B7280] bg-[#F3F4F6] border border-[#E5E7EB]">
              {processo.classeJudicial}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-8 px-3 text-xs gap-1.5 border-[#F59E0B] text-[#B45309] bg-[#FFFBEB] hover:bg-[#FEF3C7] flex-shrink-0 rounded-lg"
          >
            <Pin className="w-3.5 h-3.5" />
            Remover Lateral
          </Button>
        </div>

        {/* Objeto da ação + ação sugerida — 50/50 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 mb-4 items-start">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
              Objeto da Ação
            </p>
            <p className="text-sm text-[#374151] leading-snug">
              {processo.objetoAcao}
            </p>
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="w-0.5 h-3.5 rounded-full bg-[#EF4444] shrink-0" />
              <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase">
                Ação Sugerida
              </p>
            </div>
            <p className="text-sm font-semibold text-[#111827] leading-snug uppercase mb-2">
              {processo.proximoPasso}
            </p>
            <Button
              type="button"
              size="sm"
              onClick={() =>
                navigate({
                  to: '/elaboracao/$processoId',
                  params: { processoId: String(processoId) },
                })
              }
              className="h-7 px-3 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white text-[11px] font-semibold rounded-md"
            >
              Elaborar
            </Button>
          </div>
        </div>

        {/* Número + cliente */}
        <div className="mb-4">
          <p className="font-mono text-2xl font-bold text-[#111827] tracking-tight leading-tight">
            {processo.numero}
          </p>
          <p className="text-sm text-[#6B7280] mt-1">
            <span>Cliente Autor: </span>
            <span className="font-semibold text-[#111827]">{processo.cliente}</span>
          </p>
        </div>

        <Separator className="mb-4 bg-[#E5E7EB]" />

        {/* Metadata columns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-4">
          <div>
            <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-1.5">
              Magistrado Condutor
            </p>
            <p className="text-[13px] font-medium text-[#111827] leading-snug">
              {processo.magistrado}
            </p>
          </div>
          <div>
            <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-1.5">
              Assunto do Requerimento
            </p>
            <p className="text-[13px] font-medium text-[#111827] leading-snug">
              {processo.assunto}
            </p>
          </div>
          <div>
            <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-1.5">
              Última Atualização Técnica
            </p>
            <p className="text-[13px] font-medium text-[#111827]">
              {processo.ultimaAtualizacaoTecnica}
            </p>
          </div>
          <div>
            <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-1.5">
              Documentos do Processo
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-8 px-3 text-[11px] gap-1.5 border-[#E5E7EB] text-[#374151] hover:bg-[#F8F9FC] rounded-md"
            >
              <Download className="w-3.5 h-3.5" />
              Baixar todos PDFs
            </Button>
          </div>
        </div>

        <Separator className="mb-5 bg-[#E5E7EB]" />

        {/* Layout 40/60 — Timeline + Documents */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-6 overflow-hidden min-h-0">
          <div className="overflow-y-auto pr-1 min-h-0 lg:max-w-none">
            <MovimentacaoTimeline movimentacoes={movimentacoes} />
          </div>
          <div className="overflow-y-auto lg:pl-6 lg:border-l border-[#E5E7EB] min-h-0">
            <GabineteDocumentos
              documentos={documentos}
              ultimaMovimentacao={movimentacoes[0]?.descricao ?? ''}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
