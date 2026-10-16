import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Scale, Search } from 'lucide-react'

import { mensagemDeErro } from '#/features/auth/auth.errors'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { SecaoShell } from '#/features/secoes/SecaoShell'

import { ElaboracaoCard } from './ElaboracaoCard'
import { IniciarElaboracaoDialog } from './IniciarElaboracaoDialog'
import { modelosPeca } from './elaboracao.mock'
import { ProcessoParaIniciarCard } from './ProcessoParaIniciarCard'
import { juntarPorId } from './elaboracoes.pagina'
import {
  useCriarElaboracao,
  useElaboracoes,
  useExcluirElaboracao,
  useProcessosParaIniciar,
} from './elaboracoes.queries'
import type { ProcessoParaIniciar, RascunhoManual } from './elaboracoes.types'

const ERROS = {
  401: 'Sessão expirada. Entre novamente.',
  404: 'Elaboração não encontrada.',
}

export function ElaboracoesPage() {
  const navigate = useNavigate()
  const [texto, setTexto] = useState('')
  const [busca, setBusca] = useState('')
  const [processoAlvo, setProcessoAlvo] = useState<ProcessoParaIniciar | null>(null)
  const [erroNova, setErroNova] = useState<string | null>(null)
  const elaboracoes = useElaboracoes('')
  const paraComecar = useProcessosParaIniciar(busca)
  const excluir = useExcluirElaboracao()
  const criar = useCriarElaboracao()

  useEffect(() => {
    const id = window.setTimeout(() => setBusca(texto.trim()), 300)
    return () => window.clearTimeout(id)
  }, [texto])

  const emAndamento = elaboracoes.data ?? []
  const processos = juntarPorId((paraComecar.data?.pages ?? []).map((pagina) => pagina.items))

  function abrir(elaboracaoId: string) {
    void navigate({ to: '/elaboracao/$elaboracaoId', params: { elaboracaoId } })
  }

  async function novaElaboracao() {
    const peca = modelosPeca[0]
    const manual: RascunhoManual = {
      peca: peca.id,
      titulo: peca.nome,
      nu_processo: '',
      parte_ativa: '',
      parte_passiva: '',
      classe: '',
      assunto: '',
      foro_vara: '',
      valor_causa: '',
      juiz: '',
    }
    setErroNova(null)
    try {
      const detalhe = await criar.mutateAsync({ manual })
      abrir(detalhe.id)
    } catch (falha) {
      setErroNova(
        mensagemDeErro(falha, {
          401: 'Sessão expirada. Entre novamente.',
          422: 'Não foi possível abrir a elaboração.',
        }),
      )
    }
  }

  return (
    <SecaoShell>
      <section className="mb-6 rounded-2xl border border-[#E5E7EB] bg-white px-6 py-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB]">
              <Scale className="h-5 w-5" aria-hidden />
            </span>
            <div>
              <p className="text-[11px] font-semibold tracking-[0.18em] text-[#2563EB] uppercase">
                Elaborações
              </p>
              <h1 className="text-xl font-semibold text-[#111827]">Peças em elaboração</h1>
              <p className="mt-1 text-sm text-[#6B7280]">
                Continue uma minuta ou comece a partir de um processo.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-[#F3F4F6] px-3 py-1 text-[12px] font-semibold text-[#374151]">
              {emAndamento.length}
            </span>
            <button
              type="button"
              disabled={criar.isPending}
              onClick={() => {
                void novaElaboracao()
              }}
              className="h-9 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white transition-colors hover:bg-[#1D4ED8] active:bg-[#1E40AF] disabled:opacity-60"
            >
              {criar.isPending ? 'Abrindo…' : 'Nova elaboração'}
            </button>
          </div>
        </div>
        {erroNova ? <p className="mt-3 text-[13px] text-[#B91C1C]">{erroNova}</p> : null}
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-[13px] font-semibold tracking-wide text-[#111827] uppercase">
          Em andamento
        </h2>
        {elaboracoes.isLoading ? (
          <EstadoCarregando mensagem="Carregando elaborações…" preencher={false} />
        ) : elaboracoes.isError ? (
          <p className="text-sm text-[#6B7280]">{mensagemDeErro(elaboracoes.error, ERROS)}</p>
        ) : emAndamento.length === 0 ? (
          <p className="text-sm text-[#6B7280]">Nenhuma elaboração em andamento.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {emAndamento.map((item) => (
              <ElaboracaoCard
                key={item.id}
                elaboracao={item}
                excluindo={excluir.isPending}
                onAbrir={abrir}
                onExcluir={(id) => {
                  void excluir.mutateAsync(id)
                }}
              />
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-[13px] font-semibold tracking-wide text-[#111827] uppercase">
            Para começar
          </h2>
          <div className="relative w-full sm:w-64">
            <Search
              className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]"
              aria-hidden
            />
            <input
              value={texto}
              aria-label="Buscar por número"
              placeholder="Buscar por número"
              onChange={(event) => setTexto(event.target.value)}
              className="h-9 w-full rounded-lg border border-[#E5E7EB] bg-white pr-3 pl-9 text-[13px] text-[#111827] transition-colors outline-none placeholder:text-[#9CA3AF] hover:border-[#BFDBFE] focus:border-[#2563EB] focus:ring-2 focus:ring-[#DBEAFE]"
            />
          </div>
        </div>
        {paraComecar.isLoading ? (
          <EstadoCarregando mensagem="Carregando processos…" preencher={false} />
        ) : paraComecar.isError ? (
          <p className="text-sm text-[#6B7280]">{mensagemDeErro(paraComecar.error, ERROS)}</p>
        ) : processos.length === 0 ? (
          <p className="text-sm text-[#6B7280]">
            {busca ? 'Nenhum processo encontrado.' : 'Nenhum processo esperando para começar.'}
          </p>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {processos.map((processo) => (
                <ProcessoParaIniciarCard
                  key={processo.id}
                  processo={processo}
                  onComecar={setProcessoAlvo}
                />
              ))}
            </div>
            {paraComecar.hasNextPage ? (
              <button
                type="button"
                className="mt-4 h-9 rounded-lg border border-[#E5E7EB] bg-white px-3 text-[12px] font-semibold text-[#2563EB] transition-colors hover:border-[#93C5FD] hover:bg-[#EFF6FF] disabled:opacity-60"
                disabled={paraComecar.isFetchingNextPage}
                onClick={() => {
                  void paraComecar.fetchNextPage()
                }}
              >
                {paraComecar.isFetchingNextPage ? 'Carregando…' : 'Carregar mais'}
              </button>
            ) : null}
          </>
        )}
      </section>

      <IniciarElaboracaoDialog
        aberto={processoAlvo !== null}
        processoId={processoAlvo?.id ?? null}
        onAberto={(aberto) => {
          if (!aberto) {
            setProcessoAlvo(null)
          }
        }}
        onCriada={(id) => {
          setProcessoAlvo(null)
          abrir(id)
        }}
      />
    </SecaoShell>
  )
}
