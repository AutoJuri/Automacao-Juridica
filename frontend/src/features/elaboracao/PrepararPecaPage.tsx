import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'

import { Button } from '#/components/ui/button'
import { mensagemDeErro, MUITAS_TENTATIVAS } from '#/features/auth/auth.errors'
import { AutosDossie } from '#/features/processos/AutosDossie'
import { useDossie } from '#/features/processos/FaixaAutos'
import { dossieQueryKey, salvarRoteiro } from '#/features/processos/dossie.api'
import {
  etapaPreparacao,
  ROTEIRO_VAZIO,
  textoDoRoteiro,
  type RoteiroPeca,
} from '#/features/processos/dossie.estado'
import { buscarProcesso } from '#/features/processos/processos.api'
import { processoDetalheQueryKey } from '#/features/processos/processos.constants'
import { formatarNumeroCnj } from '#/features/processos/processos.format'
import { SecaoShell } from '#/features/secoes/SecaoShell'

import { atualizarFatosExtras, obterOuCriarElaboracao } from './elaboracao.api'
import { ELABORACOES_QUERY_KEY } from './elaboracoes.constants'
import { IniciarElaboracaoDialog } from './IniciarElaboracaoDialog'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

const ETAPAS = [
  { id: 1, titulo: 'Ler os autos' },
  { id: 2, titulo: 'Revisar o resumo' },
  { id: 3, titulo: 'Completar o roteiro' },
  { id: 4, titulo: 'Jurisprudência, se quiser' },
  { id: 5, titulo: 'Elaborar a minuta' },
] as const

function CampoRoteiro({
  rotulo,
  ajuda,
  valor,
  onChange,
  rows = 4,
}: {
  rotulo: string
  ajuda: string
  valor: string
  onChange: (valor: string) => void
  rows?: number
}) {
  return (
    <label className="block">
      <span className="text-[11px] font-semibold tracking-[0.14em] text-[#6B7280] uppercase">
        {rotulo}
      </span>
      <span className="mt-1 block text-[12px] leading-snug text-[#6B7280]">{ajuda}</span>
      <textarea
        value={valor}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        maxLength={4000}
        className={`mt-2 w-full resize-y rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      />
    </label>
  )
}

export function PrepararPecaPage({ processoId }: { processoId: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const processoQuery = useQuery({
    queryKey: processoDetalheQueryKey(processoId),
    queryFn: () => buscarProcesso(processoId),
  })
  const dossie = useDossie(processoId)
  const [roteiro, setRoteiro] = useState<RoteiroPeca>(ROTEIRO_VAZIO)
  const [hidratado, setHidratado] = useState(false)
  const [dialogo, setDialogo] = useState(false)
  const [avisoSalvo, setAvisoSalvo] = useState<string | null>(null)

  useEffect(() => {
    const dados = dossie.data
    if (!dados || hidratado) {
      return
    }
    const gravado = dados.roteiro
    const temGravado = Boolean(
      gravado && Object.values(gravado).some((valor) => valor.trim()),
    )
    const leituraComResumo =
      dados.status === 'pronto' || dados.status === 'bloqueado' || dados.status === 'limite_ia'
    setRoteiro({
      resumo: temGravado && gravado ? gravado.resumo : leituraComResumo ? dados.resumo || '' : '',
      tese: gravado?.tese ?? '',
      pedidos: gravado?.pedidos ?? '',
      acrescentar: gravado?.acrescentar ?? '',
      nao_incluir: gravado?.nao_incluir ?? '',
      jurisprudencia: gravado?.jurisprudencia ?? '',
    })
    setHidratado(true)
  }, [dossie.data, hidratado])

  const guardar = useMutation({
    mutationFn: () => salvarRoteiro(processoId, roteiro),
    onSuccess: (data) => {
      queryClient.setQueryData(dossieQueryKey(processoId), data)
      setAvisoSalvo('Roteiro guardado.')
    },
    onError: (erro) => {
      setAvisoSalvo(mensagemDeErro(erro, { 404: 'Processo não encontrado.', 429: MUITAS_TENTATIVAS }))
    },
  })

  const dados = dossie.data
  const etapa = etapaPreparacao(
    dados?.status,
    dados?.lidos ?? 0,
    dados?.total ?? 0,
    Boolean(roteiro.resumo.trim() || dados?.resumo?.trim()),
    Boolean(roteiro.tese.trim() || roteiro.pedidos.trim()),
  )
  const numero = formatarNumeroCnj(processoQuery.data?.nu_processo)

  function atualizar(campo: keyof RoteiroPeca, valor: string) {
    setAvisoSalvo(null)
    setRoteiro((atual) => ({ ...atual, [campo]: valor }))
  }

  return (
    <SecaoShell>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            to="/"
            search={{ processo: processoId }}
            className="text-[12px] font-semibold text-[#2563EB]"
          >
            Voltar ao processo
          </Link>
          <h1 className="mt-1 text-[20px] font-semibold text-[#111827]">Preparar peça</h1>
          <p className="mt-1 text-[13px] text-[#6B7280]">
            {processoQuery.isLoading ? 'Carregando processo…' : numero}
            {processoQuery.data?.de_classe ? ` · ${processoQuery.data.de_classe}` : ''}
          </p>
        </div>
      </div>

      <ol className="mb-5 grid gap-2 sm:grid-cols-5">
        {ETAPAS.map((item) => {
          const atual = item.id === etapa
          const feita =
            (item.id < etapa && item.id !== 4) ||
            (item.id === 4 && Boolean(roteiro.jurisprudencia.trim()))
          return (
            <li
              key={item.id}
              className={[
                'rounded-xl border px-3 py-2',
                atual ? 'border-[#2563EB] bg-[#EFF6FF]' : 'border-[#E5E7EB] bg-white',
              ].join(' ')}
            >
              <p className="text-[10px] font-semibold tracking-[0.14em] text-[#9CA3AF] uppercase">
                Etapa {item.id}
                {feita ? ' · feita' : ''}
                {item.id === 4 && !feita ? ' · opcional' : ''}
              </p>
              <p className="mt-0.5 text-[12px] font-semibold text-[#111827]">{item.titulo}</p>
            </li>
          )
        })}
      </ol>

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <AutosDossie processoId={processoId} />
        <section className="rounded-2xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <h2 className="text-[13px] font-semibold text-[#111827]">Roteiro da minuta</h2>
          <p className="mt-1 text-[12px] leading-relaxed text-[#6B7280]">
            Confira o resumo, ajuste o que estiver errado e acrescente o que o processo não
            mostra. A jurisprudência só entra na minuta se você colar o trecho aqui. No editor
            você ainda pode corrigir o texto na mão ou pedir uma alteração.
          </p>
          <div className="mt-4 space-y-4">
            <CampoRoteiro
              rotulo="Resumo dos autos"
              ajuda="A leitura preenche este campo. Corrija o que não estiver fiel ao processo."
              valor={roteiro.resumo}
              onChange={(valor) => atualizar('resumo', valor)}
              rows={6}
            />
            <CampoRoteiro
              rotulo="Tese"
              ajuda="O que esta peça vai sustentar, na ordem em que deve aparecer."
              valor={roteiro.tese}
              onChange={(valor) => atualizar('tese', valor)}
            />
            <CampoRoteiro
              rotulo="Pedidos"
              ajuda="O que pedir, na ordem. O que não estiver aqui não entra na minuta."
              valor={roteiro.pedidos}
              onChange={(valor) => atualizar('pedidos', valor)}
            />
            <CampoRoteiro
              rotulo="Pontos a acrescentar"
              ajuda="Fato, documento ou argumento que você tem e os autos não trouxeram."
              valor={roteiro.acrescentar}
              onChange={(valor) => atualizar('acrescentar', valor)}
            />
            <CampoRoteiro
              rotulo="Não incluir"
              ajuda="O que a minuta não pode mencionar."
              valor={roteiro.nao_incluir}
              onChange={(valor) => atualizar('nao_incluir', valor)}
            />
            <CampoRoteiro
              rotulo="Jurisprudência"
              ajuda="Opcional. Cole a ementa ou o trecho. Sem isso, a minuta não cita julgado."
              valor={roteiro.jurisprudencia}
              onChange={(valor) => atualizar('jurisprudencia', valor)}
              rows={5}
            />
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button
              type="button"
              variant="outline"
              disabled={guardar.isPending}
              onClick={() => guardar.mutate()}
            >
              {guardar.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
              Guardar roteiro
            </Button>
            {avisoSalvo ? <p className="text-[12px] text-[#6B7280]">{avisoSalvo}</p> : null}
          </div>
        </section>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
        <p className="max-w-xl text-[12px] leading-relaxed text-[#6B7280]">
          A minuta é o próximo passo. O editor abre com este roteiro, para você revisar, pedir
          mudança ou editar na mão.
        </p>
        <Button
          type="button"
          className="h-9 bg-[#2563EB] px-3 text-[12px] font-semibold text-white"
          disabled={guardar.isPending || processoQuery.isError}
          onClick={() => {
            guardar.mutate(undefined, { onSuccess: () => setDialogo(true) })
          }}
        >
          Elaborar minuta
        </Button>
      </div>

      <IniciarElaboracaoDialog
        aberto={dialogo}
        processoId={processoId}
        onAberto={setDialogo}
        aoCriar={async (sessao) => {
          const texto = textoDoRoteiro(roteiro)
          if (texto && !sessao.fatos_extras?.trim()) {
            await atualizarFatosExtras(sessao.id, texto)
          }
          await queryClient.invalidateQueries({ queryKey: ELABORACOES_QUERY_KEY })
        }}
        onCriada={(elaboracaoId) => {
          setDialogo(false)
          void navigate({ to: '/elaboracao/$elaboracaoId', params: { elaboracaoId } })
        }}
      />
    </SecaoShell>
  )
}
