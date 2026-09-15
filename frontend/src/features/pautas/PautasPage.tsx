import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, MapPin, Plus, Search, User, Video } from 'lucide-react'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { listarAudiencias } from '#/features/processos/processos.api'
import { AUDIENCIAS_QUERY_KEY } from '#/features/processos/processos.constants'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import { formatarNumeroCnj, rotuloTribunal } from '#/features/processos/processos.format'
import type { AudienciaPainel } from '#/features/processos/processos.types'
import { Input } from '#/components/ui/input'
import { PAUTAS_MOCK } from './pautas.mock'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'

export function PautasPage() {
  const [busca, setBusca] = useState('')
  const [comarca, setComarca] = useState('todas')
  const listaQuery = useQuery({
    queryKey: AUDIENCIAS_QUERY_KEY,
    queryFn: listarAudiencias,
  })

  const reais = listaQuery.data ?? []
  const usandoMock = !listaQuery.isLoading && !listaQuery.isError && reais.length === 0
  const base = usandoMock ? PAUTAS_MOCK : reais

  const comarcas = useMemo(() => {
    const unicas = new Set<string>()
    for (const item of base) {
      const rotulo = item.foro?.trim() || item.vara?.trim()
      if (rotulo) {
        unicas.add(rotulo)
      }
    }
    return [...unicas].sort((a, b) => a.localeCompare(b, 'pt-BR'))
  }, [base])

  const filtradas = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return base.filter((item) => {
      if (comarca !== 'todas') {
        const rotulo = item.foro?.trim() || item.vara?.trim() || ''
        if (rotulo !== comarca) {
          return false
        }
      }
      if (!termo) {
        return true
      }
      const haystack = [
        item.nu_processo,
        item.titulo,
        item.local,
        item.foro,
        item.vara,
        item.parte_ativa?.nome,
        item.parte_passiva?.nome,
        item.juiz,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(termo)
    })
  }, [base, busca, comarca])

  return (
    <SecaoShell>
      <section className="rounded-2xl border border-[#E5E7EB] bg-white shadow-sm px-6 py-5 mb-4">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB] shrink-0">
              <Calendar className="w-5 h-5" aria-hidden />
            </span>
            <div>
              <p className="text-[11px] font-semibold text-[#2563EB] tracking-[0.18em] uppercase">
                Agenda de sessões e audiências forenses
              </p>
              <h1 className="text-xl font-semibold text-[#111827] mt-0.5">
                Pautas de Audiências & Julgamentos
              </h1>
              <p className="text-sm text-[#6B7280] mt-1 max-w-2xl">
                Audiências já coletadas do e-SAJ (agenda e capa do CPO). Links de sala virtual
                ainda não vêm do portal.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              type="button"
              disabled
              title="Agendamento ainda não está em operação"
              className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white opacity-50"
            >
              <Plus className="w-3.5 h-3.5" aria-hidden />
              Agendar audiência
            </button>
            <span className="inline-flex h-9 items-center rounded-full border border-[#E5E7EB] px-3 text-[12px] font-semibold text-[#374151]">
              Total na pauta:{' '}
              {listaQuery.isLoading ? '…' : `${filtradas.length} audiência${filtradas.length === 1 ? '' : 's'}`}
            </span>
          </div>
        </div>

        {usandoMock ? (
          <p className="mt-4 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] px-3 py-2 text-sm text-[#92400E]">
            Nenhuma audiência coletada ainda. Os cards abaixo são <strong>dados fictícios</strong>{' '}
            só para visualizar o layout.
          </p>
        ) : null}

        <div className="flex flex-col sm:flex-row gap-3 mt-4">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF] pointer-events-none" />
            <Input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Pesquise por partes, número do processo ou vara..."
              className="pl-10 h-11 text-sm border-[#E5E7EB] bg-[#F8F9FC]"
            />
          </div>
          <select
            value={comarca}
            onChange={(e) => setComarca(e.target.value)}
            className="h-11 w-full sm:w-[240px] appearance-none rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-4 pr-8 text-sm text-[#374151] shrink-0"
            aria-label="Filtrar por comarca"
          >
            <option value="todas">Todas as Comarcas</option>
            {comarcas.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </section>

      {listaQuery.isError ? (
        <p className="text-sm text-[#9CA3AF]">
          {mensagemDeErro(listaQuery.error, { 401: 'Sessão expirada. Entre novamente.' })}
        </p>
      ) : listaQuery.isLoading ? (
        <div className="min-h-[280px] rounded-2xl border border-[#E5E7EB] bg-white shadow-sm flex flex-col">
          <EstadoCarregando mensagem="Carregando pautas…" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-6">
          {filtradas.map((item) => (
            <CardPauta key={item.id} item={item} mock={usandoMock} />
          ))}
        </div>
      )}
    </SecaoShell>
  )
}

function CardPauta({ item, mock }: { item: AudienciaPainel; mock: boolean }) {
  const partes = [
    item.parte_ativa?.nome?.trim(),
    item.parte_passiva?.nome?.trim(),
  ]
    .filter(Boolean)
    .join(' vs ')

  return (
    <article className="rounded-2xl border border-[#E5E7EB] bg-white shadow-sm p-5 flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#EFF6FF] text-[#2563EB]">
          {item.titulo}
        </span>
        <span className="inline-flex items-center gap-1 text-[13px] text-[#6B7280] tabular-nums shrink-0">
          <Calendar className="w-3.5 h-3.5" aria-hidden />
          {formatarDataHoraSP(item.data_audiencia)}
        </span>
      </div>
      <p className="font-mono text-[15px] font-bold text-[#111827]">
        {formatarNumeroCnj(item.nu_processo)}
      </p>
      <p className="text-[13px] text-[#6B7280] mt-1">{partes || 'Partes não informadas'}</p>
      <p className="text-[13px] text-[#374151] mt-3 flex gap-1.5">
        <MapPin className="w-3.5 h-3.5 text-[#9CA3AF] mt-0.5 shrink-0" aria-hidden />
        <span>
          {item.local?.trim() || [item.vara, item.foro].filter(Boolean).join(' - ') || 'Local não informado'}
        </span>
      </p>
      <p className="text-[13px] text-[#374151] mt-2 flex gap-1.5">
        <User className="w-3.5 h-3.5 text-[#9CA3AF] mt-0.5 shrink-0" aria-hidden />
        <span>{item.juiz?.trim() || 'Magistrado não informado'}</span>
      </p>
      {item.fonte === 'cpo' ? (
        <p className="text-[12px] text-[#9CA3AF] mt-2">Fonte: capa do CPO</p>
      ) : null}
      <div className="mt-4 pt-3 border-t border-[#F3F4F6] flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold text-[#15803D] border border-[#BBF7D0] bg-[#F0FDF4] rounded-md px-2 py-0.5">
          {item.tribunal ? rotuloTribunal(item.tribunal) : 'Tribunal'}
        </span>
        <button
          type="button"
          disabled
          title={
            mock
              ? 'Card ilustrativo — sem sala virtual'
              : 'O e-SAJ não entrega link de sala virtual nesta coleta'
          }
          className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white opacity-50"
        >
          <Video className="w-3.5 h-3.5" aria-hidden />
          Entrar na sala virtual
        </button>
      </div>
    </article>
  )
}
