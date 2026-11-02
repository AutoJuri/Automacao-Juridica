import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { mensagemDeErro, MUITAS_TENTATIVAS } from '#/features/auth/auth.errors'
import { formatarDataSP } from './processos.dates'
import { buscarDossie, dossieQueryKey, iniciarLeitura } from './dossie.api'
import {
  avisoStatus,
  deveAcompanhar,
  rotuloBotao,
  rotuloDocumento,
  temSemAcesso,
  textoProgresso,
} from './dossie.estado'

function useDossie(processoId: string) {
  return useQuery({
    queryKey: dossieQueryKey(processoId),
    queryFn: () => buscarDossie(processoId),
    refetchInterval: (query) => (deveAcompanhar(query.state.data?.status) ? 3000 : false),
  })
}

export function AutosDossie({ processoId }: { processoId: string }) {
  const queryClient = useQueryClient()
  const consulta = useDossie(processoId)
  const [resumoAberto, setResumoAberto] = useState(false)
  const [erroLocal, setErroLocal] = useState<string | null>(null)

  const ler = useMutation({
    mutationFn: () => iniciarLeitura(processoId),
    onSuccess: (data) => {
      setErroLocal(null)
      queryClient.setQueryData(dossieQueryKey(processoId), data)
    },
    onError: (erro) => {
      setErroLocal(
        mensagemDeErro(erro, {
          404: 'Processo não encontrado.',
          409: 'Já existe uma leitura em andamento.',
          429: MUITAS_TENTATIVAS,
        }),
      )
    },
  })

  const dados = consulta.data
  const lendo = dados?.status === 'lendo' || ler.isPending
  const aviso =
    dados?.status === 'erro' && dados.resumo
      ? dados.resumo
      : dados
        ? avisoStatus(dados.status)
        : null
  const semAcesso = temSemAcesso((dados?.documentos ?? []).map((doc) => doc.status))

  return (
    <section className="rounded-2xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-[13px] font-semibold text-[#111827]">Autos</h2>
          <p className="mt-1 text-[12px] leading-relaxed text-[#6B7280]">
            A leitura entra na mesma pasta do botão Baixar PDFs. O arquivo fica só em memória:
            guardamos uma ficha cifrada e descartamos o PDF.
          </p>
        </div>
        <Button
          type="button"
          size="sm"
          disabled={lendo || consulta.isLoading}
          onClick={() => ler.mutate()}
          className="h-9 shrink-0 bg-[#2563EB] px-3 text-[12px] font-semibold text-white"
        >
          {lendo ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
          {dados ? rotuloBotao(dados.status, dados.lidos, dados.total) : 'Ler autos'}
        </Button>
      </div>

      {consulta.isLoading ? (
        <p className="mt-3 text-[12px] text-[#9CA3AF]">Carregando autos…</p>
      ) : null}

      {consulta.isError ? (
        <p className="mt-3 text-[12px] text-[#B91C1C]">
          {mensagemDeErro(consulta.error, { 404: 'Processo não encontrado.' })}
        </p>
      ) : null}

      {erroLocal ? <p className="mt-3 text-[12px] text-[#B91C1C]">{erroLocal}</p> : null}

      {aviso ? (
        <p className="mt-3 text-[12px] leading-relaxed text-[#6B7280]">
          {aviso}{' '}
          {dados?.status === 'sessao_expirada' ? (
            <Link to="/configuracoes" className="font-semibold text-[#2563EB]">
              Abrir configurações
            </Link>
          ) : null}
        </p>
      ) : null}

      {dados && dados.total > 0 ? (
        <p className="mt-3 text-[12px] font-medium text-[#374151]">
          {textoProgresso(dados.lidos, dados.total)}
        </p>
      ) : null}

      {semAcesso ? (
        <p className="mt-2 text-[12px] leading-relaxed text-[#6B7280]">
          Há documento que o e-SAJ só abre com a senha dos autos. A plataforma não pede nem guarda
          essa senha.
        </p>
      ) : null}

      {dados && dados.documentos.length > 0 ? (
        <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto">
          {dados.documentos.map((doc) => (
            <li key={doc.movimentacao_id} className="flex items-baseline justify-between gap-3 text-[12px]">
              <span className="min-w-0 text-[#111827]">
                {doc.data ? (
                  <span className="text-[#9CA3AF]">{formatarDataSP(doc.data)} </span>
                ) : null}
                {doc.titulo?.trim() || 'Documento sem título'}
              </span>
              <span className="shrink-0 text-[#6B7280]">{rotuloDocumento(doc.status)}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {dados?.resumo && aviso !== dados.resumo ? (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setResumoAberto((aberto) => !aberto)}
            className="text-[12px] font-semibold text-[#2563EB]"
          >
            {resumoAberto ? 'Ocultar resumo' : 'Ver resumo'}
          </button>
          {resumoAberto ? (
            <p className="mt-2 whitespace-pre-wrap text-[13px] leading-relaxed text-[#111827]">
              {dados.resumo}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
