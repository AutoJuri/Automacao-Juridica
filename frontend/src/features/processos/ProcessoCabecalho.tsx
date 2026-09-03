import { Download, Pin, WandSparkles } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '#/components/ui/button'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { AudienciaCpoLista } from './AudienciaCpoLista'
import { AudienciaLista } from './AudienciaLista'
import { IntimacaoTimeline } from './IntimacaoTimeline'
import { PeticoesDiversasLista } from './PeticoesDiversasLista'
import { atualizarFixado } from './processos.api'
import { PROCESSOS_QUERY_KEY, processoDetalheQueryKey } from './processos.constants'
import { formatarDataHoraSP, textoCampoCpo } from './processos.dates'
import {
  formatarNumeroCnj,
  juntarLocalProcesso,
  rotuloGrau,
  rotuloPortal,
  tagTribunalGrau,
} from './processos.format'
import type { ParteCpoPublica, ProcessoDetalhe } from './processos.types'
import { urlEsajHttps } from './processos.urls'

const PLACEHOLDER = 'Não disponível'

interface ProcessoCabecalhoProps {
  processo: ProcessoDetalhe
}

function CampoMeta({ rotulo, valor }: { rotulo: string; valor: string }) {
  const vazio = valor === PLACEHOLDER || valor === 'Ainda não buscado no CPO'
  return (
    <div className="min-w-0">
      <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1.5">
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

export function ProcessoCabecalho({ processo }: ProcessoCabecalhoProps) {
  const queryClient = useQueryClient()
  const cpoPendente = processo.movimentacoes_status === 'pendente'
  const campoCpo = (valor: string | null | undefined) => textoCampoCpo(valor, cpoPendente)
  const numero = formatarNumeroCnj(processo.nu_processo)
  const classe = processo.de_classe?.trim() || PLACEHOLDER
  const hrefPasta = urlEsajHttps(processo.url_pasta)
  const local = juntarLocalProcesso(
    processo.foro?.trim() ?? '',
    processo.area?.trim() ?? '',
    processo.vara?.trim() ?? '',
  )
  const localExibicao = local || (cpoPendente ? 'Ainda não buscado no CPO' : PLACEHOLDER)

  const fixar = useMutation({
    mutationFn: (proximo: boolean) => atualizarFixado(processo.id, proximo),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROCESSOS_QUERY_KEY })
      void queryClient.invalidateQueries({ queryKey: processoDetalheQueryKey(processo.id) })
    },
  })

  const erroFixar = fixar.isError
    ? mensagemDeErro(fixar.error, { 401: 'Sessão expirada. Entre novamente.' })
    : null

  return (
    <section className="shrink-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm px-6 py-5">
      <div className="flex items-start gap-6">
        <div className="flex-1 min-w-0">
          <div className="flex items-center flex-wrap gap-2 mb-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-semibold text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
              {tagTribunalGrau(processo.tribunal, processo.instancia)}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-semibold text-[#374151] bg-[#F3F4F6] border border-[#E5E7EB]">
              {rotuloPortal(processo.tribunal)}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] font-semibold tracking-wide text-[#6B7280] bg-[#F3F4F6] border border-[#E5E7EB]">
              {classe}
            </span>
          </div>

          <div className="flex items-center gap-2 min-w-0">
            <p className="font-mono text-[22px] sm:text-2xl font-bold text-[#111827] tracking-tight leading-tight truncate">
              {numero}
            </p>
            <button
              type="button"
              onClick={() => fixar.mutate(!processo.fixado)}
              disabled={fixar.isPending}
              aria-pressed={processo.fixado}
              aria-label={processo.fixado ? 'Desfixar processo' : 'Fixar processo'}
              title={processo.fixado ? 'Desfixar processo' : 'Fixar processo'}
              className={[
                'inline-flex h-8 w-8 items-center justify-center rounded-lg border transition-colors shrink-0',
                processo.fixado
                  ? 'border-[#BFDBFE] bg-[#EFF6FF] text-[#2563EB]'
                  : 'border-[#E5E7EB] bg-white text-[#9CA3AF] hover:border-[#BFDBFE] hover:text-[#2563EB]',
              ].join(' ')}
            >
              <Pin className={['w-4 h-4', processo.fixado ? 'fill-current' : ''].join(' ')} />
            </button>
          </div>
          {erroFixar ? <p className="text-[11px] text-[#B91C1C] mt-1">{erroFixar}</p> : null}

          <p
            className={[
              'text-[13px] mt-1.5',
              local ? 'text-[#6B7280]' : 'text-[#9CA3AF] italic',
            ].join(' ')}
          >
            {localExibicao}
          </p>

          <div className="h-px bg-[#E5E7EB] my-4" />

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-4">
            <CampoMeta
              rotulo="Polo ativo (autor)"
              valor={processo.parte_ativa?.nome?.trim() || PLACEHOLDER}
            />
            <CampoMeta
              rotulo="Polo passivo (réu)"
              valor={processo.parte_passiva?.nome?.trim() || PLACEHOLDER}
            />
            <CampoMeta rotulo="Magistrado Condutor" valor={campoCpo(processo.juiz)} />
            <CampoMeta
              rotulo="Assunto do Requerimento"
              valor={processo.de_assunto?.trim() || PLACEHOLDER}
            />
            <CampoMeta
              rotulo="Última Atualização Técnica"
              valor={formatarDataHoraSP(processo.last_synced_at)}
            />
            <CampoMeta
              rotulo="Instância"
              valor={rotuloGrau(processo.instancia) || PLACEHOLDER}
            />
            <CampoMeta rotulo="Controle" valor={campoCpo(processo.controle)} />
            <CampoMeta rotulo="Valor da ação" valor={campoCpo(processo.valor_acao)} />
          </div>
        </div>

        <div className="w-[200px] shrink-0 flex flex-col items-stretch gap-3 border-l border-[#E5E7EB] pl-5">
          {hrefPasta ? (
            <a
              href={hrefPasta}
              target="_blank"
              rel="noreferrer"
              title="Abre a pasta digital no e-SAJ. Os PDFs não passam pelo nosso servidor."
              className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-semibold text-[#111827] hover:bg-[#F8F9FC]"
            >
              <Download className="w-3.5 h-3.5" aria-hidden />
              Baixar PDFs
            </a>
          ) : (
            <Button
              type="button"
              variant="outline"
              disabled
              title="Pasta digital ainda não disponível neste processo"
              className="h-9 px-3 text-[12px] font-semibold border-[#E5E7EB] text-[#9CA3AF]"
            >
              <Download className="w-3.5 h-3.5" aria-hidden />
              Baixar PDFs
            </Button>
          )}

          <div>
            <p className="text-[9px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
              Ação sugerida
            </p>
            <p className="text-[13px] text-[#9CA3AF] italic leading-snug">{PLACEHOLDER}</p>
          </div>

          <Button
            asChild
            size="sm"
            className="h-9 px-3 bg-[#2563EB] text-white text-[12px] font-semibold rounded-lg"
          >
            <Link to="/elaboracao/$processoId" params={{ processoId: processo.id }}>
              <WandSparkles className="w-3.5 h-3.5" aria-hidden />
              Elaborar
            </Link>
          </Button>
        </div>
      </div>

      {processo.sem_incidentes === true || processo.sem_apensos === true ? (
        <p className="text-[12px] text-[#6B7280] leading-relaxed mt-4 whitespace-pre-wrap">
          {processo.sem_incidentes === true ? 'Não há incidentes neste processo.' : null}
          {processo.sem_incidentes === true && processo.sem_apensos === true ? ' ' : null}
          {processo.sem_apensos === true ? 'Não há apensos neste processo.' : null}
        </p>
      ) : null}

      <details className="mt-4 group">
        <summary className="cursor-pointer list-none text-[11px] font-semibold text-[#6B7280] tracking-wide uppercase select-none hover:text-[#111827] [&::-webkit-details-marker]:hidden">
          <span className="inline-flex items-center gap-2">
            Agenda, intimações, petições e partes
            <span className="text-[#9CA3AF] font-medium normal-case tracking-normal">
              (dados já coletados)
            </span>
          </span>
        </summary>
        <div className="mt-4 pt-4 border-t border-[#E5E7EB]">
          <PartesCpo partes={processo.partes_cpo ?? []} pendente={cpoPendente} />
          <AudienciaLista audiencias={processo.audiencias} />
          <AudienciaCpoLista
            audiencias={processo.audiencias_cpo ?? []}
            status={processo.movimentacoes_status}
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <IntimacaoTimeline key={processo.id} intimacoes={processo.intimacoes} />
            <PeticoesDiversasLista
              peticoes={processo.peticoes_diversas ?? []}
              status={processo.movimentacoes_status}
            />
          </div>
        </div>
      </details>
    </section>
  )
}
