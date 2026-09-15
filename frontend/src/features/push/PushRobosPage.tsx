import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FastForward, Loader2, Plus, RefreshCw } from 'lucide-react'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { listarProcessos } from '#/features/processos/processos.api'
import { PROCESSOS_QUERY_KEY } from '#/features/processos/processos.constants'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import { formatarNumeroCnj, rotuloTribunal } from '#/features/processos/processos.format'
import { buscarStatusCredenciais } from '#/features/settings/credentials.api'
import { CREDENTIALS_STATUS_QUERY_KEY } from '#/features/settings/credentials.constants'
import { Input } from '#/components/ui/input'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'

export function PushRobosPage() {
  const [avisoForm, setAvisoForm] = useState(false)
  const processosQuery = useQuery({
    queryKey: PROCESSOS_QUERY_KEY,
    queryFn: () => listarProcessos(),
  })
  const credQuery = useQuery({
    queryKey: CREDENTIALS_STATUS_QUERY_KEY,
    queryFn: buscarStatusCredenciais,
  })

  const processos = processosQuery.data ?? []
  const sessao = credQuery.data
  const esajOk = Boolean(sessao?.cadastrado && sessao.session_status === 'ativo' && !sessao.sessao_expirada)

  return (
    <SecaoShell>
      <p className="mb-4 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] px-4 py-2.5 text-sm text-[#92400E] leading-relaxed">
        Os processos à direita são os já acompanhados pelo ciclo real. O formulário, o botão
        de varredura forçada e os status PJe são <strong>só visualização</strong> — dados
        ilustrativos, sem cadastro novo e sem WhatsApp.
      </p>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-5">
        <div className="flex gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[#F3E8FF] text-[#7C3AED] shrink-0">
            <FastForward className="w-5 h-5" aria-hidden />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-[#7C3AED]">
              Push e Monitoramento Processual Contínuo
            </h1>
            <p className="text-sm text-[#6B7280] mt-1 max-w-2xl">
              O scheduler já varre o e-SAJ em ciclo. Esta tela não dispara Playwright nem
              envia alerta externo.
            </p>
          </div>
        </div>
        <button
          type="button"
          disabled
          title="A varredura continua no scheduler. Não disparamos Playwright daqui."
          className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#7C3AED] px-3 text-[13px] font-semibold text-white opacity-50 shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" aria-hidden />
          Forçar varredura agora
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(20rem,32%)_1fr] gap-4 pb-6">
        <div className="space-y-4">
          <section className="rounded-2xl border border-[#E5E7EB] bg-white shadow-sm p-5">
            <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-4">
              Adicionar ao push robótico
            </p>
            <label className="block text-[13px] font-medium text-[#374151] mb-1">
              Número do processo (CNJ)
            </label>
            <Input placeholder="Ex: 1004521-89.2026.8.26.0100" className="mb-3 h-10 bg-[#F8F9FC] text-sm" disabled />
            <label className="block text-[13px] font-medium text-[#374151] mb-1">
              Cliente / referência interna
            </label>
            <Input placeholder="Ex: Acme Industrial S.A." className="mb-3 h-10 bg-[#F8F9FC] text-sm" disabled />
            <div className="grid grid-cols-2 gap-2 mb-4">
              <select disabled className="h-10 rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 text-sm text-[#6B7280]">
                <option>TJSP (e-SAJ)</option>
              </select>
              <select disabled className="h-10 rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 text-sm text-[#6B7280]">
                <option>WhatsApp (ilustrativo)</option>
              </select>
            </div>
            <button
              type="button"
              onClick={() => setAvisoForm(true)}
              className="w-full inline-flex h-10 items-center justify-center gap-1.5 rounded-lg bg-[#7C3AED] text-[13px] font-semibold text-white"
            >
              <Plus className="w-3.5 h-3.5" aria-hidden />
              Cadastrar processo no push
            </button>
            {avisoForm ? (
              <p className="text-[13px] text-[#92400E] mt-2">
                Cadastro ilustrativo — nenhum processo novo é gravado.
              </p>
            ) : null}
          </section>

          <section className="rounded-2xl border border-[#E5E7EB] bg-white shadow-sm p-5">
            <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-3">
              Estado do cluster headless
            </p>
            <ul className="space-y-3">
              <li className="flex items-center justify-between gap-2 text-sm">
                <span className="text-[#111827]">e-SAJ TJSP (São Paulo)</span>
                {credQuery.isLoading ? (
                  <span className="inline-flex items-center gap-1.5 text-[13px] text-[#6B7280]">
                    <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" aria-hidden />
                    Carregando
                  </span>
                ) : esajOk ? (
                  <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#15803D]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
                    Sessão ativa
                  </span>
                ) : (
                  <span className="text-[13px] font-semibold text-[#B45309]">
                    {sessao?.session_status ?? 'Sem sessão'}
                  </span>
                )}
              </li>
              <li className="flex items-center justify-between gap-2 text-sm">
                <span className="text-[#6B7280]">PJe TRF3 (Federal)</span>
                <span className="text-[13px] text-[#9CA3AF]">Ilustrativo</span>
              </li>
              <li className="flex items-center justify-between gap-2 text-sm">
                <span className="text-[#6B7280]">PJe TRT2 (Trabalhista)</span>
                <span className="text-[13px] text-[#9CA3AF]">Ilustrativo</span>
              </li>
            </ul>
          </section>
        </div>

        <section className="min-h-0 flex flex-col">
          <p className="text-[11px] font-semibold text-[#6B7280] tracking-[0.18em] uppercase mb-3">
            Monitoramentos ativos ({processosQuery.isLoading ? '…' : processos.length})
          </p>
          {processosQuery.isError ? (
            <p className="text-sm text-[#9CA3AF]">
              {mensagemDeErro(processosQuery.error, { 401: 'Sessão expirada. Entre novamente.' })}
            </p>
          ) : processosQuery.isLoading ? (
            <div className="min-h-[280px] rounded-2xl border border-[#E5E7EB] bg-white shadow-sm flex flex-col">
              <EstadoCarregando mensagem="Carregando processos…" />
            </div>
          ) : processos.length === 0 ? (
            <p className="text-sm text-[#9CA3AF]">Nenhum processo coletado ainda.</p>
          ) : (
            <div className="space-y-3">
              {processos.map((processo) => (
                <article
                  key={processo.id}
                  className="rounded-2xl border border-[#E5E7EB] bg-white shadow-sm p-5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <span className="inline-flex px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#F3E8FF] text-[#7C3AED]">
                        {rotuloTribunal(processo.tribunal)} + e-SAJ
                      </span>
                      <p className="font-mono text-[15px] font-bold text-[#111827] mt-2">
                        {formatarNumeroCnj(processo.nu_processo)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#15803D]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
                        Monitorando ativo
                      </span>
                      <span
                        className="text-[13px] font-semibold text-[#9CA3AF]"
                        title="Pausa ilustrativa — o ciclo continua no scheduler"
                      >
                        Pausar
                      </span>
                    </div>
                  </div>
                  <p className="text-[13px] text-[#6B7280] mt-2">
                    Cliente: {processo.parte_ativa?.nome?.trim() || 'Não informado'}
                  </p>
                  <div className="mt-3 rounded-lg bg-[#F8F9FC] border border-[#E5E7EB] px-3 py-2.5">
                    <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.14em] uppercase mb-1">
                      Último andamento capturado
                    </p>
                    <p className="text-[13px] text-[#374151] leading-relaxed">
                      {processo.ultima_atividade?.titulo?.trim() || 'Ainda sem evento coletado'}
                    </p>
                  </div>
                  <p className="text-[13px] text-[#9CA3AF] mt-2">
                    Última sincronização:{' '}
                    {processo.last_synced_at
                      ? formatarDataHoraSP(processo.last_synced_at)
                      : 'Não disponível'}
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </SecaoShell>
  )
}
