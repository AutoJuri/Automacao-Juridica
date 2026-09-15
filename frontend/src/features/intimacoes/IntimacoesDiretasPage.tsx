import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Check, Search, Send, TriangleAlert } from 'lucide-react'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { listarIntimacoes } from '#/features/processos/processos.api'
import { INTIMACOES_QUERY_KEY } from '#/features/processos/processos.constants'
import { formatarDataHoraSP, formatarDataSP } from '#/features/processos/processos.dates'
import {
  formatarNumeroCnj,
  rotuloTribunal,
  tagTribunalGrau,
} from '#/features/processos/processos.format'
import type { IntimacaoPainel } from '#/features/processos/processos.types'
import { Input } from '#/components/ui/input'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'

export function IntimacoesDiretasPage() {
  const [busca, setBusca] = useState('')
  const [soPendentes, setSoPendentes] = useState(false)
  const [selecionadoId, setSelecionadoId] = useState<string | null>(null)

  const listaQuery = useQuery({
    queryKey: INTIMACOES_QUERY_KEY,
    queryFn: listarIntimacoes,
  })

  const intimacoes = listaQuery.data ?? []
  const pendentes = intimacoes.filter((item) => !item.ciencia).length

  const filtradas = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return intimacoes.filter((item) => {
      if (soPendentes && item.ciencia) {
        return false
      }
      if (!termo) {
        return true
      }
      const haystack = [
        item.nu_processo,
        item.titulo,
        item.descricao,
        item.vara,
        item.foro,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(termo)
    })
  }, [intimacoes, busca, soPendentes])

  useEffect(() => {
    if (filtradas.some((item) => item.id === selecionadoId)) {
      return
    }
    setSelecionadoId(filtradas[0]?.id ?? null)
  }, [filtradas, selecionadoId])

  const selecionada = filtradas.find((item) => item.id === selecionadoId) ?? null

  return (
    <SecaoShell scroll={false}>
      <div className="flex flex-col gap-4 flex-1 min-h-0">
        <section className="shrink-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm px-6 py-5">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold text-[#B45309] tracking-[0.18em] uppercase mb-1">
                Painel de comunicações e citações eletrônicas
              </p>
              <h1 className="text-xl font-semibold text-[#111827]">
                Intimações Diretas dos Tribunais (Sem DJE)
              </h1>
              <p className="text-sm text-[#6B7280] mt-1 max-w-2xl">
                Intimações já coletadas pelo ciclo. Ciência formal e peticionamento ainda
                não são feitos daqui — o e-SAJ continua sendo o canal oficial.
              </p>
            </div>
            <div className="rounded-xl border border-[#FDE68A] bg-[#FFFBEB] px-4 py-3 min-w-[180px]">
              <p className="text-[11px] font-semibold text-[#92400E] tracking-[0.16em] uppercase">
                Sem ciência
              </p>
              <p className="text-base font-semibold text-[#111827] mt-0.5">
                {listaQuery.isLoading
                  ? '…'
                  : `${pendentes} ${pendentes === 1 ? 'comunicação' : 'comunicações'}`}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <div className="relative flex-1 min-w-0">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF] pointer-events-none" />
              <Input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Pesquisar por número do processo, teor ou vara..."
                className="pl-10 h-11 text-sm border-[#E5E7EB] bg-[#F8F9FC]"
              />
            </div>
            <div className="flex rounded-lg border border-[#E5E7EB] p-1 bg-[#F8F9FC] shrink-0">
              <FiltroChip
                ativo={!soPendentes}
                onClick={() => setSoPendentes(false)}
                label={`Todas (${intimacoes.length})`}
              />
              <FiltroChip
                ativo={soPendentes}
                onClick={() => setSoPendentes(true)}
                label={`Pendentes (${pendentes})`}
              />
            </div>
          </div>
        </section>

        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(26rem,38%)_1fr] gap-5">
          <section className="min-h-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 flex flex-col">
              {listaQuery.isError ? (
                <p className="text-sm text-[#9CA3AF]">
                  {mensagemDeErro(listaQuery.error, { 401: 'Sessão expirada. Entre novamente.' })}
                </p>
              ) : listaQuery.isLoading ? (
                <EstadoCarregando mensagem="Carregando intimações…" />
              ) : filtradas.length === 0 ? (
                <p className="text-sm text-[#9CA3AF]">
                  Nenhuma intimação coletada para estes filtros.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {filtradas.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelecionadoId(item.id)}
                      className={[
                        'w-full text-left rounded-xl p-4 border bg-white transition-all cursor-pointer',
                        item.id === selecionadoId
                          ? 'border-[#2563EB] shadow-sm ring-1 ring-[#2563EB]/15'
                          : 'border-[#E5E7EB] hover:border-[#C7D0E8] hover:bg-[#F8F9FC]',
                      ].join(' ')}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#EFF6FF] text-[#2563EB]">
                          {item.tribunal ? rotuloTribunal(item.tribunal) : 'Tribunal'}
                        </span>
                        <span
                          className={[
                            'inline-flex items-center gap-1 text-[11px] font-semibold rounded-full px-2 py-0.5 border',
                            item.ciencia
                              ? 'bg-[#F0FDF4] text-[#15803D] border-[#BBF7D0]'
                              : 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]',
                          ].join(' ')}
                        >
                          {item.ciencia ? 'Ciência tomada' : 'Sem ciência'}
                        </span>
                      </div>
                      <p className="font-mono text-[15px] font-bold text-[#111827]">
                        {formatarNumeroCnj(item.nu_processo)}
                      </p>
                      <p className="text-[13px] text-[#6B7280] mt-1 line-clamp-2">
                        {item.titulo?.trim() || item.descricao?.trim() || 'Intimação'}
                      </p>
                      <div className="flex justify-between gap-2 mt-2 text-[12px] text-[#9CA3AF]">
                        <span className="truncate">{item.vara?.trim() || item.foro?.trim() || '—'}</span>
                        <span className="tabular-nums shrink-0">
                          {item.data_movimentacao ? formatarDataSP(item.data_movimentacao) : '—'}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="min-h-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm overflow-y-auto px-6 py-5 flex flex-col">
            {listaQuery.isLoading ? (
              <EstadoCarregando mensagem="Carregando detalhes…" />
            ) : selecionada ? (
              <DetalheIntimacao item={selecionada} />
            ) : (
              <p className="text-sm text-[#9CA3AF]">Selecione uma intimação à esquerda.</p>
            )}
          </section>
        </div>
      </div>
    </SecaoShell>
  )
}

function FiltroChip({
  ativo,
  onClick,
  label,
}: {
  ativo: boolean
  onClick: () => void
  label: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'h-8 px-3 rounded-md text-[13px] font-semibold',
        ativo ? 'bg-[#2563EB] text-white' : 'text-[#4B5563]',
      ].join(' ')}
    >
      {label}
    </button>
  )
}

function DetalheIntimacao({ item }: { item: IntimacaoPainel }) {
  const orgao = [item.tribunal ? rotuloTribunal(item.tribunal) : null, item.vara || item.foro]
    .filter(Boolean)
    .join(' · ')

  return (
    <div>
      <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
        Detalhes da comunicação eletrônica
      </p>
      <p className="font-mono text-xl font-bold text-[#111827] mt-1">
        {formatarNumeroCnj(item.nu_processo)}
      </p>
      <p className="text-[13px] text-[#6B7280] mt-0.5">
        {tagTribunalGrau(item.tribunal ?? '', item.instancia)}
      </p>

      {item.ciencia ? (
        <div className="mt-4 rounded-xl border border-[#BBF7D0] bg-[#F0FDF4] px-4 py-3 flex gap-2">
          <Check className="w-4 h-4 text-[#15803D] mt-0.5 shrink-0" aria-hidden />
          <p className="text-sm text-[#166534] leading-relaxed">
            Ciência já registrada no e-SAJ para esta intimação.
          </p>
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-[#FDE68A] bg-[#FFFBEB] px-4 py-3 flex gap-2">
          <TriangleAlert className="w-4 h-4 text-[#B45309] mt-0.5 shrink-0" aria-hidden />
          <p className="text-sm text-[#92400E] leading-relaxed">
            Ciência ainda não registrada no e-SAJ. O prazo e a tomada de ciência formal
            continuam no portal — não calculamos prazo daqui.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5 pt-4 border-t border-[#E5E7EB]">
        <div>
          <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
            Tribunal / órgão
          </p>
          <p className="text-[14px] font-medium text-[#111827]">{orgao || 'Não disponível'}</p>
        </div>
        <div>
          <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
            Disponibilização
          </p>
          <p className="text-[14px] font-medium text-[#111827]">
            {formatarDataHoraSP(item.data_movimentacao)}
          </p>
        </div>
      </div>

      <div className="mt-5">
        <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
          Teor da intimação
        </p>
        <div className="rounded-xl border border-[#E5E7EB] bg-[#FAFAFA] px-4 py-3 min-h-[160px]">
          <p className="text-[14px] font-semibold text-[#111827] mb-2">
            {item.titulo?.trim() || 'Intimação'}
          </p>
          <p className="text-[14px] text-[#374151] leading-relaxed whitespace-pre-wrap">
            {item.descricao?.trim() || 'Sem texto adicional nesta intimação.'}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mt-5">
        <button
          type="button"
          disabled
          title="Dar ciência continua no e-SAJ. Não protocolamos ICP-Brasil daqui."
          className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#EA580C] px-3 text-[12px] font-semibold text-white opacity-50"
        >
          <Check className="w-3.5 h-3.5" aria-hidden />
          Dar ciência formal agora (ICP-Brasil)
        </button>
        <button
          type="button"
          disabled
          title="Peticionamento ainda não está em operação"
          className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white opacity-50"
        >
          <Send className="w-3.5 h-3.5" aria-hidden />
          Peticionar resposta / recurso
        </button>
      </div>
    </div>
  )
}
