import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Download,
  Eye,
  FileText,
  Search,
  Sparkles,
} from 'lucide-react'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { VisualizadorPdfModal } from '#/features/processos/VisualizadorPdfModal'
import { buscarProcesso, listarProcessos } from '#/features/processos/processos.api'
import {
  PROCESSOS_QUERY_KEY,
  processoDetalheQueryKey,
} from '#/features/processos/processos.constants'
import { formatarDataSP, textoCampoCpo } from '#/features/processos/processos.dates'
import {
  formatarNumeroCnj,
  juntarLocalProcesso,
  rotuloGrau,
  rotuloPortal,
  rotuloTribunal,
  tagTribunalGrau,
} from '#/features/processos/processos.format'
import type { MovimentacaoPublica, ProcessoLista } from '#/features/processos/processos.types'
import { hrefDocumentoMovimentacao, urlEsajHttps } from '#/features/processos/processos.urls'
import { portaisDisponiveis, type PortalKey } from '#/features/processos/portais.mock'
import { Input } from '#/components/ui/input'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'

const PLACEHOLDER = 'Não disponível'

interface PecaPasta {
  id: string
  nome: string
  detalhe: string
  href: string | null
  movimentacao: MovimentacaoPublica | null
}

export function ConsultaPastaPage() {
  const [busca, setBusca] = useState('')
  const [buscaDebounced, setBuscaDebounced] = useState('')
  const [tipoBusca, setTipoBusca] = useState<'cnj' | 'partes' | 'livre'>('cnj')
  const [portal, setPortal] = useState<PortalKey>('todos')
  const [selecionadoId, setSelecionadoId] = useState<string | null>(null)
  const [pecaModal, setPecaModal] = useState<PecaPasta | null>(null)

  useEffect(() => {
    const handle = window.setTimeout(() => setBuscaDebounced(busca), 300)
    return () => window.clearTimeout(handle)
  }, [busca])

  const listaQuery = useQuery({
    queryKey: [...PROCESSOS_QUERY_KEY, 'consulta', buscaDebounced],
    queryFn: () => listarProcessos(buscaDebounced),
  })

  const processos = useMemo(() => {
    const itens = listaQuery.data ?? []
    if (portal === 'todos') {
      return itens
    }
    return itens.filter((item) => item.tribunal === portal)
  }, [listaQuery.data, portal])

  useEffect(() => {
    if (processos.some((p) => p.id === selecionadoId)) {
      return
    }
    setSelecionadoId(processos[0]?.id ?? null)
  }, [processos, selecionadoId])

  const detalheQuery = useQuery({
    queryKey: selecionadoId ? processoDetalheQueryKey(selecionadoId) : ['processos', 'consulta-nenhum'],
    queryFn: () => buscarProcesso(selecionadoId as string),
    enabled: Boolean(selecionadoId),
  })

  const pecas = useMemo(() => montarPecas(detalheQuery.data), [detalheQuery.data])

  return (
    <SecaoShell scroll={false}>
      <div className="flex flex-col gap-4 flex-1 min-h-0">
        <section className="shrink-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm px-6 py-5">
          <p className="text-[11px] font-semibold text-[#2563EB] tracking-[0.18em] uppercase mb-1">
            Motor de indexação e-SAJ / PJe / Tribunais
          </p>
          <h1 className="text-xl font-semibold text-[#111827]">
            Consulta Processual Unificada & Pasta Digital
          </h1>
          <p className="text-sm text-[#6B7280] mt-1 max-w-2xl">
            Busca nos processos já coletados. Documentos abrem no e-SAJ — nada é baixado
            pelo nosso servidor.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <select
              value={tipoBusca}
              onChange={(e) => setTipoBusca(e.target.value as 'cnj' | 'partes' | 'livre')}
              className="h-11 w-full sm:w-[220px] appearance-none rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-4 pr-8 text-sm text-[#374151] shrink-0"
              aria-label="Tipo de busca"
            >
              <option value="cnj">Número do Processo (CNJ)</option>
              <option value="partes">Nome das partes</option>
              <option value="livre">Consulta livre</option>
            </select>
            <div className="relative flex-1 min-w-0">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF] pointer-events-none" />
              <Input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder={
                  tipoBusca === 'partes'
                    ? 'Digite o nome das partes...'
                    : tipoBusca === 'livre'
                      ? 'Digite CNJ, partes, classe ou OAB...'
                      : 'Digite o número CNJ, nome das partes ou OAB...'
                }
                className="pl-10 h-11 text-sm border-[#E5E7EB] bg-[#F8F9FC]"
              />
            </div>
            <select
              value={portal}
              onChange={(e) => setPortal(e.target.value as PortalKey)}
              className="h-11 w-full sm:w-[220px] appearance-none rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-4 pr-8 text-sm text-[#374151]"
              aria-label="Filtrar por tribunal"
            >
              {portaisDisponiveis.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </section>

        <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(26rem,38%)_1fr] gap-5">
          <section className="min-h-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm flex flex-col overflow-hidden">
            <div className="px-5 pt-5 pb-3 shrink-0">
              <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
                Autos localizados ({listaQuery.isLoading ? '…' : processos.length})
              </p>
            </div>
            <div className="flex-1 overflow-y-auto px-4 pb-4 flex flex-col">
              {listaQuery.isError ? (
                <p className="text-sm text-[#9CA3AF] px-1">
                  {mensagemDeErro(listaQuery.error, { 401: 'Sessão expirada. Entre novamente.' })}
                </p>
              ) : listaQuery.isLoading ? (
                <EstadoCarregando mensagem="Carregando processos…" />
              ) : processos.length === 0 ? (
                <p className="text-sm text-[#9CA3AF] px-1">
                  Nenhum processo coletado para estes filtros.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {processos.map((processo) => (
                    <CardConsulta
                      key={processo.id}
                      processo={processo}
                      selecionado={processo.id === selecionadoId}
                      onClick={() => setSelecionadoId(processo.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="min-h-0 rounded-2xl border border-[#E5E7EB] bg-white shadow-sm overflow-y-auto px-6 py-5 flex flex-col">
            {!selecionadoId ? (
              <p className="text-sm text-[#9CA3AF]">Selecione um processo à esquerda.</p>
            ) : detalheQuery.isLoading ? (
              <EstadoCarregando mensagem="Carregando ficha…" />
            ) : detalheQuery.isError || !detalheQuery.data ? (
              <p className="text-sm text-[#9CA3AF]">
                {mensagemDeErro(detalheQuery.error, { 404: 'Processo não encontrado.' })}
              </p>
            ) : (
              <FichaConsulta
                pecas={pecas}
                onAbrirPeca={setPecaModal}
                processo={detalheQuery.data}
              />
            )}
          </section>
        </div>
      </div>

      {pecaModal?.movimentacao ? (
        <VisualizadorPdfModal
          aberto
          onFechar={() => setPecaModal(null)}
          movimentacao={pecaModal.movimentacao}
          numeroProcesso={detalheQuery.data?.nu_processo ?? null}
          hrefDocumento={pecaModal.href}
        />
      ) : null}
    </SecaoShell>
  )
}

function CardConsulta({
  processo,
  selecionado,
  onClick,
}: {
  processo: ProcessoLista
  selecionado: boolean
  onClick: () => void
}) {
  const grau = rotuloGrau(processo.instancia)
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'w-full text-left rounded-xl p-4 border bg-white transition-all cursor-pointer',
        selecionado
          ? 'border-[#2563EB] shadow-sm ring-1 ring-[#2563EB]/15'
          : 'border-[#E5E7EB] hover:border-[#C7D0E8] hover:bg-[#F8F9FC]',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#F3F4F6] border border-[#E5E7EB] text-[#374151]">
            {rotuloTribunal(processo.tribunal)}
          </span>
          <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#EFF6FF] text-[#2563EB]">
            {rotuloPortal(processo.tribunal)}
          </span>
        </div>
        {grau ? (
          <span className="text-[11px] font-semibold text-[#15803D] bg-[#F0FDF4] border border-[#BBF7D0] rounded-md px-2 py-0.5">
            {grau}
          </span>
        ) : null}
      </div>
      <p className="font-mono text-[15px] font-bold text-[#111827]">
        {formatarNumeroCnj(processo.nu_processo)}
      </p>
      <p className="text-[13px] text-[#6B7280] mt-1.5">
        Autor: {processo.parte_ativa?.nome?.trim() || PLACEHOLDER}
      </p>
      <p className="text-[13px] text-[#6B7280]">
        Réu: {processo.parte_passiva?.nome?.trim() || PLACEHOLDER}
      </p>
      <div className="flex items-center justify-between gap-2 mt-2 text-[12px] text-[#9CA3AF]">
        <span className="truncate">{processo.de_classe?.trim() || '—'}</span>
        <span className="tabular-nums shrink-0">
          {processo.last_synced_at ? formatarDataSP(processo.last_synced_at) : '—'}
        </span>
      </div>
    </button>
  )
}

function FichaConsulta({
  processo,
  pecas,
  onAbrirPeca,
}: {
  processo: import('#/features/processos/processos.types').ProcessoDetalhe
  pecas: PecaPasta[]
  onAbrirPeca: (peca: PecaPasta) => void
}) {
  const cpoPendente = processo.movimentacoes_status === 'pendente'
  const local = juntarLocalProcesso(
    processo.foro?.trim() ?? '',
    processo.area?.trim() ?? '',
    processo.vara?.trim() ?? '',
  )
  const hrefPasta = urlEsajHttps(processo.url_pasta)
  const advogadoAtivo = processo.partes_cpo.find((p) =>
    /autor|reqte|ativo/i.test(p.papel),
  )?.advogados
  const advogadoPassivo = processo.partes_cpo.find((p) =>
    /réu|reu|reqdo|passivo/i.test(p.papel),
  )?.advogados

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="inline-flex px-2.5 py-0.5 rounded-md text-[12px] font-semibold text-[#2563EB] bg-[#EFF6FF] border border-[#BFDBFE]">
              {tagTribunalGrau(processo.tribunal, processo.instancia)}
            </span>
            <span className="inline-flex px-2.5 py-0.5 rounded-md text-[12px] font-semibold text-[#1E3A8A] bg-[#F3F4F6] border border-[#E5E7EB]">
              {processo.de_classe?.trim() || PLACEHOLDER}
            </span>
          </div>
          <p className="font-mono text-2xl font-bold text-[#111827] tracking-tight">
            {formatarNumeroCnj(processo.nu_processo)}
          </p>
          <p className={['text-sm mt-1', local ? 'text-[#6B7280]' : 'text-[#9CA3AF] italic'].join(' ')}>
            {local || (cpoPendente ? 'Ainda não buscado no CPO' : PLACEHOLDER)}
          </p>
        </div>
        <div className="flex flex-col gap-2 shrink-0">
          <button
            type="button"
            disabled
            title="Diagnóstico por IA ainda não está em operação"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#7C3AED] px-3 text-[12px] font-semibold text-white opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" aria-hidden />
            Diagnóstico IA (Gemini)
          </button>
          <button
            type="button"
            disabled
            title="Peticionamento ainda não está em operação"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white opacity-50"
          >
            <FileText className="w-3.5 h-3.5" aria-hidden />
            Peticionar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
        <Campo
          rotulo="Polo ativo (autor)"
          valor={processo.parte_ativa?.nome?.trim() || PLACEHOLDER}
          extra={advogadoAtivo}
          caixa
        />
        <Campo
          rotulo="Polo passivo (réu)"
          valor={processo.parte_passiva?.nome?.trim() || PLACEHOLDER}
          extra={advogadoPassivo}
          caixa
        />
      </div>
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 rounded-xl border border-[#E5E7EB] divide-y sm:divide-y-0 xl:divide-x divide-[#E5E7EB] overflow-hidden">
        <Campo rotulo="Valor da causa" valor={textoCampoCpo(processo.valor_acao, cpoPendente)} faixa />
        <Campo rotulo="Distribuição" valor={textoCampoCpo(processo.distribuicao, cpoPendente)} faixa />
        <Campo rotulo="Magistrado" valor={textoCampoCpo(processo.juiz, cpoPendente)} faixa />
        <Campo rotulo="Assunto" valor={processo.de_assunto?.trim() || PLACEHOLDER} faixa />
      </div>

      <div className="mt-6 pt-4 border-t border-[#E5E7EB]">
        <div className="flex items-center justify-between gap-3 mb-3">
          <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase">
            Pasta digital de documentos ({pecas.length} {pecas.length === 1 ? 'peça' : 'peças'})
          </p>
          {hrefPasta ? (
            <a
              href={hrefPasta}
              target="_blank"
              rel="noreferrer"
              title="Abre a pasta digital no e-SAJ. Não geramos ZIP no servidor."
              className="inline-flex items-center gap-1 text-[13px] font-semibold text-[#2563EB] hover:underline"
            >
              <Download className="w-3.5 h-3.5" aria-hidden />
              Abrir pasta no e-SAJ
            </a>
          ) : (
            <span className="text-[13px] text-[#9CA3AF]">Pasta digital ainda não disponível</span>
          )}
        </div>
        {pecas.length === 0 ? (
          <p className="text-sm text-[#9CA3AF]">
            Nenhuma peça coletada para listar. Use o link da pasta no e-SAJ quando existir.
          </p>
        ) : (
          <ul className="divide-y divide-[#F3F4F6] rounded-xl border border-[#E5E7EB]">
            {pecas.map((peca) => (
              <li key={peca.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <div className="min-w-0 flex items-start gap-3">
                  <FileText className="w-4 h-4 text-[#2563EB] mt-0.5 shrink-0" aria-hidden />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[#111827] truncate">{peca.nome}</p>
                    <p className="text-[13px] text-[#6B7280]">{peca.detalhe}</p>
                  </div>
                </div>
                {peca.movimentacao ? (
                  <button
                    type="button"
                    onClick={() => onAbrirPeca(peca)}
                    className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white shrink-0"
                  >
                    <Eye className="w-3.5 h-3.5" aria-hidden />
                    Visualizar
                  </button>
                ) : peca.href ? (
                  <a
                    href={peca.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white shrink-0"
                  >
                    <Eye className="w-3.5 h-3.5" aria-hidden />
                    Visualizar
                  </a>
                ) : (
                  <span className="text-[13px] text-[#9CA3AF] shrink-0">Sem link</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function Campo({
  rotulo,
  valor,
  extra,
  caixa = false,
  faixa = false,
}: {
  rotulo: string
  valor: string
  extra?: string | null
  caixa?: boolean
  faixa?: boolean
}) {
  const vazio = valor === PLACEHOLDER || valor === 'Ainda não buscado no CPO'
  return (
    <div
      className={[
        'min-w-0',
        caixa ? 'rounded-xl border border-[#E5E7EB] bg-[#F8F9FC] px-4 py-3' : '',
        faixa ? 'px-4 py-3' : '',
      ].join(' ')}
    >
      <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.16em] uppercase mb-1">
        {rotulo}
      </p>
      <p className={['text-[14px]', vazio ? 'text-[#9CA3AF] italic' : 'font-medium text-[#111827]'].join(' ')}>
        {valor}
      </p>
      {extra?.trim() ? <p className="text-[13px] text-[#6B7280] mt-0.5 whitespace-pre-wrap">{extra.trim()}</p> : null}
    </div>
  )
}

function montarPecas(
  processo: import('#/features/processos/processos.types').ProcessoDetalhe | undefined,
): PecaPasta[] {
  if (!processo) {
    return []
  }
  const pecas: PecaPasta[] = []
  for (const item of processo.movimentacoes) {
    if (!item.tem_documento) {
      continue
    }
    const href = hrefDocumentoMovimentacao(item.tem_documento, item.url_documento, processo.url_cpo)
    pecas.push({
      id: `mov-${item.id}`,
      nome: `${item.titulo?.trim() || 'Movimentação'}.pdf`,
      detalhe: [formatarDataSP(item.data_movimentacao), 'Documento no e-SAJ'].join(' · '),
      href,
      movimentacao: item,
    })
  }
  for (const item of processo.peticoes_diversas) {
    pecas.push({
      id: `pet-${item.id}`,
      nome: item.tipo.trim() || 'Petição',
      detalhe: [formatarDataSP(item.data_peticao), item.protocolo?.trim() || 'Sem protocolo']
        .filter(Boolean)
        .join(' · '),
      href: urlEsajHttps(processo.url_cpo) ?? urlEsajHttps(processo.url_pasta),
      movimentacao: null,
    })
  }
  return pecas
}
