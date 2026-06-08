import { useState } from 'react'
import { Search, Pin, ChevronDown } from 'lucide-react'
import { Input } from '#/components/ui/input'
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
  const [searchQuery, setSearchQuery] = useState('')

  const processo = processosMockados.find((p) => p.id === processoId)
  const movimentacoes = movimentacoesMockadas.filter((m) => m.processoId === processoId)
  const documentos = documentosMockados.filter((d) => d.processoId === processoId)

  if (!processo) {
    return (
      <div className="flex-1 flex items-center justify-center rounded-xl border border-[#E5E7EB] bg-white">
        <p className="text-[#9CA3AF] text-sm">Selecione um processo na barra lateral.</p>
      </div>
    )
  }

  return (
    <main className="flex-1 flex flex-col gap-4 overflow-hidden min-w-0">
      {/* ── Seção superior: Árbitro de Pesquisa (card) ── */}
      <div className="rounded-xl border border-[#E5E7EB] bg-white px-6 py-5 shadow-sm">
        <p className="text-[10px] font-semibold text-[#3B5BDB] tracking-[0.2em] uppercase mb-1">
          Árbitro de Pesquisa
        </p>
        <h1 className="text-xl font-semibold text-[#111827] mb-4">
          Consulta Unificada de Autos Legistas
        </h1>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Pesquise por número do processo, cliente autor ou tribunal..."
              className="pl-10 h-11 text-sm border-[#E5E7EB] bg-[#F8F9FC] text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB] rounded-lg"
            />
          </div>
          <Button
            variant="outline"
            className="h-11 px-4 text-sm border-[#E5E7EB] text-[#374151] gap-2 hover:bg-[#F8F9FC] whitespace-nowrap rounded-lg"
          >
            Visualizar Todos
            <ChevronDown className="w-4 h-4 text-[#9CA3AF]" />
          </Button>
        </div>
      </div>

      {/* ── Seção inferior: Detalhe do processo (card) ── */}
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

          {/* Process number + client */}
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
          <div className="grid grid-cols-3 gap-6 mb-4">
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
          </div>

          <Separator className="mb-5 bg-[#E5E7EB]" />

          {/* ── Two-column layout: Timeline + Documents ── */}
          <div className="flex-1 grid grid-cols-2 gap-6 overflow-hidden min-h-0">
            <div className="overflow-y-auto pr-1 min-h-0">
              <MovimentacaoTimeline movimentacoes={movimentacoes} />
            </div>
            <div className="overflow-y-auto pl-6 border-l border-[#E5E7EB] min-h-0">
              <GabineteDocumentos
                documentos={documentos}
                ultimaMovimentacao={movimentacoes[0]?.descricao ?? ''}
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
