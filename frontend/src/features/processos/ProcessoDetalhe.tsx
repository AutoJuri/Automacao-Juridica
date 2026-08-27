import { Pin } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '#/components/ui/button'
import { Separator } from '#/components/ui/separator'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { AudienciaCpoLista } from './AudienciaCpoLista'
import { AudienciaLista } from './AudienciaLista'
import { GabineteDocumentos } from './GabineteDocumentos'
import { IntimacaoTimeline } from './IntimacaoTimeline'
import { MovimentacoesTimeline } from './MovimentacoesTimeline'
import { PeticoesDiversasLista } from './PeticoesDiversasLista'
import { buscarProcesso } from './processos.api'
import { processoDetalheQueryKey } from './processos.constants'
import { formatarDataHoraSP, textoCampoCpo } from './processos.dates'
import type { ParteCpoPublica } from './processos.types'

interface ProcessoDetalheProps {
  processoId: string | null
}

const TRIBUNAL_ROTULO: Record<string, string> = {
  esaj_tjsp: 'TJSP',
}

const PLACEHOLDER = 'Não disponível'

function CampoMeta({ rotulo, valor }: { rotulo: string; valor: string }) {
  const vazio = valor === PLACEHOLDER || valor === 'Ainda não buscado no CPO'
  return (
    <div>
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-1.5">
        {rotulo}
      </p>
      <p
        className={[
          'text-[13px] leading-snug whitespace-pre-wrap',
          vazio ? 'text-[#9CA3AF] italic' : 'font-medium text-[#111827]',
        ].join(' ')}
      >
        {valor}
      </p>
    </div>
  )
}

function PartesCpo({ partes, pendente }: { partes: ParteCpoPublica[]; pendente: boolean }) {
  return (
    <div className="mb-4">
      <p className="text-[10px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-2">
        Partes do processo
      </p>
      {partes.length === 0 ? (
        <p className="text-[12px] text-[#9CA3AF] leading-relaxed">
          {pendente ? 'Ainda não buscado no CPO' : PLACEHOLDER}
        </p>
      ) : (
        <ul className="space-y-2">
          {partes.map((parte, indice) => (
            <li key={`${parte.papel}-${indice}`} className="text-[13px] leading-snug">
              <p className="text-[11px] font-semibold text-[#6B7280] uppercase tracking-wide">
                {parte.papel}
              </p>
              <p className="text-[#111827] whitespace-pre-wrap">{parte.nome?.trim() || PLACEHOLDER}</p>
              {parte.advogados?.trim() ? (
                <p className="text-[12px] text-[#6B7280] whitespace-pre-wrap mt-0.5">
                  {parte.advogados.trim()}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function ProcessoDetalhe({ processoId }: ProcessoDetalheProps) {
  const detalheQuery = useQuery({
    queryKey: processoId ? processoDetalheQueryKey(processoId) : ['processos', 'nenhum'],
    queryFn: () => buscarProcesso(processoId as string),
    enabled: Boolean(processoId),
  })

  if (!processoId) {
    return (
      <div className="flex-1 flex items-center justify-center rounded-xl border border-[#E5E7EB] bg-white min-h-[200px]">
        <p className="text-[#9CA3AF] text-sm px-6 text-center">
          Nenhum processo selecionado ou nenhum resultado para os filtros aplicados.
        </p>
      </div>
    )
  }

  if (detalheQuery.isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center rounded-xl border border-[#E5E7EB] bg-white min-h-[200px]">
        <p className="text-[#9CA3AF] text-sm">Carregando processo…</p>
      </div>
    )
  }

  if (detalheQuery.isError || !detalheQuery.data) {
    return (
      <div className="flex-1 flex items-center justify-center rounded-xl border border-[#E5E7EB] bg-white min-h-[200px]">
        <p className="text-[#9CA3AF] text-sm px-6 text-center">
          {mensagemDeErro(detalheQuery.error, { 404: 'Processo não encontrado.' })}
        </p>
      </div>
    )
  }

  const processo = detalheQuery.data
  const cliente = processo.parte_ativa?.nome?.trim() || 'Não informado'
  const reu = processo.parte_passiva?.nome?.trim()
  const numero = processo.nu_processo?.trim() || 'Número não informado'
  const tribunal = TRIBUNAL_ROTULO[processo.tribunal] ?? processo.tribunal.toUpperCase()
  const cpoPendente = processo.movimentacoes_status === 'pendente'
  const campoCpo = (valor: string | null | undefined) => textoCampoCpo(valor, cpoPendente)

  return (
    <div className="flex-1 flex flex-col overflow-hidden rounded-xl border border-[#E5E7EB] bg-white shadow-sm min-h-0">
      <div className="flex-1 overflow-y-auto px-6 pt-5 pb-5 min-h-0">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center flex-wrap gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-semibold text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
              {tribunal}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] font-semibold tracking-wide text-[#6B7280] bg-[#F3F4F6] border border-[#E5E7EB]">
              {processo.de_classe?.trim() || PLACEHOLDER}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled
            className="h-8 px-3 text-xs gap-1.5 border-[#E5E7EB] text-[#9CA3AF] bg-white flex-shrink-0 rounded-lg"
          >
            <Pin className="w-3.5 h-3.5" />
            Remover Lateral
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 mb-4 items-start">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
              Objeto da Ação
            </p>
            <p className="text-sm text-[#9CA3AF] leading-snug italic">{PLACEHOLDER}</p>
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="w-0.5 h-3.5 rounded-full bg-[#D1D5DB] shrink-0" />
              <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase">
                Ação Sugerida
              </p>
            </div>
            <p className="text-sm text-[#9CA3AF] leading-snug italic mb-2">{PLACEHOLDER}</p>
            <Button
              type="button"
              size="sm"
              disabled
              title="Elaboração de peças ainda usa dados mockados e fica para a próxima etapa"
              className="h-7 px-3 bg-[#E5E7EB] text-[#9CA3AF] text-[11px] font-semibold rounded-md"
            >
              Elaborar
            </Button>
          </div>
        </div>

        <div className="mb-4">
          <p className="font-mono text-2xl font-bold text-[#111827] tracking-tight leading-tight">
            {numero}
          </p>
          <p className="text-sm text-[#6B7280] mt-1">
            <span>Cliente Autor: </span>
            <span className="font-semibold text-[#111827]">{cliente}</span>
          </p>
          {reu ? (
            <p className="text-sm text-[#6B7280] mt-0.5">
              <span>Parte passiva: </span>
              <span className="font-semibold text-[#111827]">{reu}</span>
            </p>
          ) : null}
        </div>

        <PartesCpo partes={processo.partes_cpo ?? []} pendente={cpoPendente} />

        <Separator className="mb-4 bg-[#E5E7EB]" />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-4">
          <CampoMeta rotulo="Magistrado Condutor" valor={campoCpo(processo.juiz)} />
          <CampoMeta
            rotulo="Assunto do Requerimento"
            valor={processo.de_assunto?.trim() || PLACEHOLDER}
          />
          <CampoMeta rotulo="Última Atualização Técnica" valor={formatarDataHoraSP(processo.last_synced_at)} />
          <CampoMeta rotulo="Instância" valor={processo.instancia?.trim() || PLACEHOLDER} />
          <CampoMeta rotulo="Foro" valor={campoCpo(processo.foro)} />
          <CampoMeta rotulo="Vara" valor={campoCpo(processo.vara)} />
          <CampoMeta rotulo="Área" valor={campoCpo(processo.area)} />
          <CampoMeta rotulo="Valor da ação" valor={campoCpo(processo.valor_acao)} />
          <CampoMeta rotulo="Distribuição" valor={campoCpo(processo.distribuicao)} />
          <CampoMeta rotulo="Controle" valor={campoCpo(processo.controle)} />
        </div>

        {processo.sem_incidentes === true || processo.sem_apensos === true ? (
          <p className="text-[12px] text-[#6B7280] leading-relaxed mb-4 whitespace-pre-wrap">
            {processo.sem_incidentes === true ? 'Não há incidentes neste processo.' : null}
            {processo.sem_incidentes === true && processo.sem_apensos === true ? ' ' : null}
            {processo.sem_apensos === true ? 'Não há apensos neste processo.' : null}
          </p>
        ) : null}

        <Separator className="mb-5 bg-[#E5E7EB]" />

        <AudienciaLista audiencias={processo.audiencias} />
        <AudienciaCpoLista
          audiencias={processo.audiencias_cpo ?? []}
          status={processo.movimentacoes_status}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="pr-1 min-w-0">
            <MovimentacoesTimeline
              key={processo.id}
              movimentacoes={processo.movimentacoes}
              status={processo.movimentacoes_status}
              urlCpo={processo.url_cpo}
            />
          </div>
          <div className="lg:pl-6 lg:border-l border-[#E5E7EB] min-w-0">
            <IntimacaoTimeline key={processo.id} intimacoes={processo.intimacoes} />
          </div>
          <div className="lg:pl-6 lg:border-l border-[#E5E7EB] min-w-0">
            <PeticoesDiversasLista
              peticoes={processo.peticoes_diversas ?? []}
              status={processo.movimentacoes_status}
            />
            <GabineteDocumentos urlCpo={processo.url_cpo} urlPasta={processo.url_pasta} />
          </div>
        </div>
      </div>
    </div>
  )
}
