import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { mensagemDeErro } from '#/features/auth/auth.errors'
import { listarOrganizacoes } from '#/features/organizations/organizations.api'
import { ORGANIZATIONS_QUERY_KEY } from '#/features/organizations/organizations.constants'
import { podeGerenciar } from '#/features/organizations/organizations.roles'
import { formatarNumeroCnj } from '#/features/processos/processos.format'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { useAuthStore } from '#/store/auth.store'
import { useOrgStore } from '#/store/org.store'

import { ajustarTotais } from './tarefas.board'
import { KanbanBoard } from './KanbanBoard'
import { QuadroCabecalho } from './QuadroCabecalho'
import { TarefaDetalheDialog } from './TarefaDetalheDialog'
import { TarefaDialog } from './TarefaDialog'
import type { CorpoTarefa } from './tarefas.api'
import {
  useAtualizarColuna,
  useAtualizarQuadro,
  useAtualizarTarefa,
  useCarregarMaisConcluidas,
  useCriarColuna,
  useCriarTarefa,
  useExcluirTarefa,
  useMembrosParaTarefas,
  useMoverTarefa,
  useProcessosParaTarefas,
  useQuadroTarefas,
  useRemoverColuna,
} from './tarefas.queries'
import type { Quadro, RascunhoTarefa, Tarefa } from './tarefas.types'

type Dialogo =
  | { tipo: 'criar'; colunaId: string }
  | { tipo: 'editar'; tarefa: Tarefa }
  | { tipo: 'ver'; tarefa: Tarefa }
  | null

const ERROS_COLUNA = {
  403: 'Sem permissão para alterar as colunas.',
  409: 'Não foi possível alterar a coluna. Ela pode ter tarefas ou o quadro já chegou no limite.',
}

export function TarefasPage() {
  const usuario = useAuthStore((estado) => estado.user)
  const orgId = useOrgStore((estado) => estado.activeOrganizationId)
  const quadroQuery = useQuadroTarefas(orgId, usuario?.id)
  const [dialogo, setDialogo] = useState<Dialogo>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  const membrosQuery = useMembrosParaTarefas(orgId)
  const processosQuery = useProcessosParaTarefas()
  const organizacoes = useQuery({
    queryKey: ORGANIZATIONS_QUERY_KEY,
    queryFn: listarOrganizacoes,
    enabled: orgId !== null,
  })
  const criar = useCriarTarefa(orgId)
  const atualizar = useAtualizarTarefa(orgId)
  const excluir = useExcluirTarefa(orgId)
  const mover = useMoverTarefa(orgId)
  const carregarMais = useCarregarMaisConcluidas(orgId, orgId === null, usuario?.id ?? '')
  const criarColuna = useCriarColuna(orgId)
  const atualizarColuna = useAtualizarColuna(orgId)
  const removerColuna = useRemoverColuna(orgId)
  const atualizarQuadro = useAtualizarQuadro(orgId)

  const membros = membrosQuery.data ?? []
  const processos = processosQuery.data ?? []
  const pessoal = orgId === null
  const papel = organizacoes.data?.find((org) => org.id === orgId)?.role
  const podeConfigurar = pessoal || podeGerenciar(papel)

  function falhaDeColuna(erro: unknown) {
    setAviso(mensagemDeErro(erro, ERROS_COLUNA))
  }

  async function salvar(rascunho: RascunhoTarefa, tarefaId: string | null) {
    const colunaId = tarefaId
      ? quadroQuery.data?.tarefas.find((item) => item.id === tarefaId)?.colunaId
      : dialogo?.tipo === 'criar'
        ? dialogo.colunaId
        : null
    if (!colunaId) {
      return
    }
    const corpo = corpoDaTarefa(rascunho, colunaId, pessoal)
    if (tarefaId) {
      const { column_id: _coluna, ...alteracao } = corpo
      await atualizar.mutateAsync({ tarefaId, corpo: alteracao })
      return
    }
    await criar.mutateAsync(corpo)
  }

  if (!usuario) {
    return null
  }

  if (quadroQuery.isError) {
    return (
      <SecaoShell scroll={false}>
        <div className="flex flex-1 flex-col items-center justify-center">
          <p className="text-sm text-[#B91C1C]">Não foi possível carregar o quadro.</p>
          <button
            type="button"
            className="mt-3 text-sm font-semibold text-[#2563EB]"
            onClick={() => void quadroQuery.refetch()}
          >
            Tentar de novo
          </button>
        </div>
      </SecaoShell>
    )
  }

  if (!quadroQuery.data) {
    return (
      <SecaoShell scroll={false}>
        <EstadoCarregando mensagem="Carregando o quadro…" />
      </SecaoShell>
    )
  }

  const quadro = quadroQuery.data
  const usuarioAtual = usuario
  const total = quadro.colunas.reduce((soma, coluna) => soma + coluna.total, 0)

  function nomeResponsavel(responsavelId: string): string {
    if (pessoal && responsavelId === usuarioAtual.id) {
      return usuarioAtual.name
    }
    return membros.find((membro) => membro.id === responsavelId)?.name ?? 'Responsável indisponível'
  }

  function rotuloProcesso(processoId: string | null): string | null {
    if (!processoId) {
      return null
    }
    const numero = quadro.tarefas.find((item) => item.processoId === processoId)?.processoNumero
    if (numero) {
      return formatarNumeroCnj(numero)
    }
    const processo = processos.find((item) => item.id === processoId)
    if (!processo) {
      return 'Processo indisponível'
    }
    return formatarNumeroCnj(processo.nu_processo)
  }

  function aoMover(proximo: Quadro, tarefaId: string) {
    const tarefa = proximo.tarefas.find((item) => item.id === tarefaId)
    if (!tarefa) {
      return
    }
    const posicao = proximo.tarefas
      .filter((item) => item.colunaId === tarefa.colunaId)
      .findIndex((item) => item.id === tarefaId)
    const coluna = proximo.colunas.find((item) => item.id === tarefa.colunaId)
    const origemId = quadro.tarefas.find((item) => item.id === tarefaId)?.colunaId ?? tarefa.colunaId
    const ajustado: Quadro = ajustarTotais(
      {
        ...proximo,
        tarefas: proximo.tarefas.map((item) =>
          item.id === tarefaId ? { ...item, concluida: Boolean(coluna?.conclusao) } : item,
        ),
      },
      origemId,
      tarefa.colunaId,
    )
    setAviso(null)
    mover.mutate(
      { tarefaId, colunaId: tarefa.colunaId, posicao, proximo: ajustado },
      {
        onError: (erro) => {
          setAviso(
            mensagemDeErro(erro, {
              403: 'Sem permissão para mover esta tarefa.',
              404: 'Essa tarefa ou coluna não está mais no quadro.',
            }),
          )
        },
      },
    )
  }

  const tarefaVista = dialogo?.tipo === 'ver' ? dialogo.tarefa : null
  const formularioAberto = dialogo?.tipo === 'criar' || dialogo?.tipo === 'editar'

  return (
    <SecaoShell scroll={false}>
      <QuadroCabecalho
        titulo={quadro.titulo}
        descricao={quadro.descricao}
        total={total}
        podeEditar={podeConfigurar}
        salvando={atualizarQuadro.isPending}
        onSalvar={async (titulo, descricao) => {
          setAviso(null)
          await atualizarQuadro.mutateAsync({ title: titulo, description: descricao })
        }}
      />
      {aviso ? <p className="mb-3 text-sm text-[#B91C1C]">{aviso}</p> : null}
      {membrosQuery.isError ? (
        <p className="mb-3 text-sm text-[#9CA3AF]">
          {mensagemDeErro(membrosQuery.error, { 401: 'Sessão expirada. Entre novamente.' })}
        </p>
      ) : null}

      <KanbanBoard
        quadro={quadro}
        podeConfigurar={podeConfigurar}
        onMover={aoMover}
        onAdicionarColuna={() => {
          setAviso(null)
          criarColuna.mutate('Nova coluna', { onError: falhaDeColuna })
        }}
        nomeResponsavel={nomeResponsavel}
        rotuloProcesso={rotuloProcesso}
        onRenomear={(colunaId, titulo) => {
          setAviso(null)
          atualizarColuna.mutate({ colunaId, title: titulo.trim() }, { onError: falhaDeColuna })
        }}
        onRemover={(colunaId) => {
          setAviso(null)
          removerColuna.mutate(colunaId, { onError: falhaDeColuna })
        }}
        onMarcarConclusao={(colunaId) => {
          setAviso(null)
          atualizarColuna.mutate({ colunaId, is_done: true }, { onError: falhaDeColuna })
        }}
        onNovaTarefa={(colunaId) => setDialogo({ tipo: 'criar', colunaId })}
        onAbrirTarefa={(tarefa) => setDialogo({ tipo: 'ver', tarefa })}
        onEditarTarefa={(tarefa) => setDialogo({ tipo: 'editar', tarefa })}
        onExcluirTarefa={(tarefaId) => {
          setAviso(null)
          excluir.mutate(tarefaId, {
            onError: (erro) => {
              setAviso(
                mensagemDeErro(erro, {
                  403: 'Sem permissão para excluir esta tarefa.',
                  404: 'Essa tarefa não está mais no quadro.',
                }),
              )
            },
          })
        }}
        carregandoMais={carregarMais.isPending}
        onCarregarMais={(colunaId) => {
          setAviso(null)
          const carregadas = quadro.tarefas.filter((item) => item.colunaId === colunaId).length
          carregarMais.mutate(
            { colunaId, offset: carregadas },
            {
              onError: (erro) => {
                setAviso(mensagemDeErro(erro, { 404: 'Essa coluna não está mais no quadro.' }))
              },
            },
          )
        }}
      />

      <TarefaDetalheDialog
        tarefa={tarefaVista}
        colunaNome={quadro.colunas.find((coluna) => coluna.id === tarefaVista?.colunaId)?.titulo ?? ''}
        responsavelNome={
          tarefaVista ? tarefaVista.responsavelNome || nomeResponsavel(tarefaVista.responsavelId) : ''
        }
        processoRotulo={tarefaVista ? rotuloProcesso(tarefaVista.processoId) : null}
        onAberto={(aberto) => {
          if (!aberto) {
            setDialogo(null)
          }
        }}
        onEditar={(tarefa) => setDialogo({ tipo: 'editar', tarefa })}
        onExcluir={async (tarefaId) => {
          await excluir.mutateAsync(tarefaId)
        }}
      />

      <TarefaDialog
        aberto={formularioAberto}
        colunaId={dialogo?.tipo === 'criar' ? dialogo.colunaId : (dialogo?.tipo === 'editar' ? dialogo.tarefa.colunaId : null)}
        tarefa={dialogo?.tipo === 'editar' ? dialogo.tarefa : null}
        pessoal={pessoal}
        usuario={usuario}
        membros={membros}
        processos={processos}
        onAberto={(aberto) => {
          if (!aberto) {
            setDialogo(null)
          }
        }}
        onSalvar={salvar}
        onExcluir={async (tarefaId) => {
          await excluir.mutateAsync(tarefaId)
        }}
      />
    </SecaoShell>
  )
}

function corpoDaTarefa(rascunho: RascunhoTarefa, colunaId: string, pessoal: boolean): CorpoTarefa {
  return {
    title: rascunho.titulo.trim(),
    description: rascunho.descricao.trim(),
    column_id: colunaId,
    due_date: rascunho.prazo,
    processo_id: rascunho.processoId,
    ...(pessoal ? {} : { assigned_to_member_id: rascunho.responsavelId }),
  }
}
