import { useEffect, useMemo, useState } from 'react'

import { Button } from '#/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '#/components/ui/dialog'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '#/components/ui/select'
import { Textarea } from '#/components/ui/textarea'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import type { AuthUser } from '#/store/auth.store'
import type { MemberPublic } from '#/features/organizations/organizations.types'
import { formatarNumeroCnj } from '#/features/processos/processos.format'
import type { ProcessoLista } from '#/features/processos/processos.types'

import { LIMITE_DESCRICAO, LIMITE_TITULO_TAREFA, validarRascunho } from './tarefas.board'
import type { RascunhoTarefa, Tarefa } from './tarefas.types'

interface TarefaDialogProps {
  aberto: boolean
  colunaId: string | null
  tarefa: Tarefa | null
  pessoal: boolean
  usuario: AuthUser
  membros: MemberPublic[]
  processos: ProcessoLista[]
  onAberto: (aberto: boolean) => void
  onSalvar: (rascunho: RascunhoTarefa, tarefaId: string | null) => Promise<void>
  onExcluir: (tarefaId: string) => Promise<void>
}

export function TarefaDialog(props: TarefaDialogProps) {
  return (
    <Dialog open={props.aberto} onOpenChange={props.onAberto}>
      <DialogContent className="sm:max-w-lg">
        {props.aberto && props.colunaId ? <FormularioTarefa {...props} colunaId={props.colunaId} /> : null}
      </DialogContent>
    </Dialog>
  )
}

function FormularioTarefa({
  tarefa,
  pessoal,
  usuario,
  membros,
  processos,
  onAberto,
  onSalvar,
  onExcluir,
}: TarefaDialogProps & { colunaId: string }) {
  const responsavelInicial = tarefa?.responsavelId ?? responsavelPadrao(pessoal, usuario, membros)
  const [titulo, setTitulo] = useState(tarefa?.titulo ?? '')
  const [descricao, setDescricao] = useState(tarefa?.descricao ?? '')
  const [responsavelId, setResponsavelId] = useState(responsavelInicial)
  const [processoId, setProcessoId] = useState<string | null>(tarefa?.processoId ?? null)
  const [prazo, setPrazo] = useState(tarefa?.prazo ?? '')
  const [buscaProcesso, setBuscaProcesso] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState(false)
  const [confirmarExclusao, setConfirmarExclusao] = useState(false)

  useEffect(() => {
    if (pessoal || responsavelId || membros.length === 0) {
      return
    }
    setResponsavelId(responsavelPadrao(false, usuario, membros))
  }, [membros, pessoal, responsavelId, usuario])

  const processosFiltrados = useMemo(() => filtrarProcessos(processos, buscaProcesso), [processos, buscaProcesso])
  const processoSelecionado = processos.find((processo) => processo.id === processoId) ?? null

  async function salvar() {
    const rascunho: RascunhoTarefa = {
      titulo,
      descricao,
      responsavelId: pessoal ? usuario.id : responsavelId,
      processoId,
      prazo: prazo || null,
    }
    const mensagem = validarRascunho(rascunho)
    if (mensagem) {
      setErro(mensagem)
      return
    }
    if (!pessoal && !membros.some((membro) => membro.id === rascunho.responsavelId)) {
      setErro('Escolha um membro desta organização.')
      return
    }
    if (processoId && !processos.some((processo) => processo.id === processoId)) {
      setErro('Escolha um processo da sua lista.')
      return
    }
    setSalvando(true)
    try {
      await onSalvar(rascunho, tarefa?.id ?? null)
      onAberto(false)
    } catch (falha) {
      setErro(
        mensagemDeErro(falha, {
          400: 'Escolha um membro desta organização.',
          403: 'Sem permissão para esta ação.',
          404: 'Não encontramos essa tarefa ou esse processo.',
        }),
      )
    } finally {
      setSalvando(false)
    }
  }

  async function excluir() {
    if (!tarefa) {
      return
    }
    if (!confirmarExclusao) {
      setConfirmarExclusao(true)
      return
    }
    setSalvando(true)
    try {
      await onExcluir(tarefa.id)
      onAberto(false)
    } catch (falha) {
      setConfirmarExclusao(false)
      setErro(
        mensagemDeErro(falha, {
          403: 'Sem permissão para excluir esta tarefa.',
          404: 'Essa tarefa não está mais no quadro.',
        }),
      )
    } finally {
      setSalvando(false)
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{tarefa ? 'Editar tarefa' : 'Nova tarefa'}</DialogTitle>
        <DialogDescription>
          Título, quem vai fazer e, se quiser, um processo e um prazo. A descrição é texto livre.
        </DialogDescription>
      </DialogHeader>

      <div className="grid gap-3">
        <div className="grid gap-1.5">
          <Label htmlFor="tarefa-titulo">Título</Label>
          <Input
            id="tarefa-titulo"
            value={titulo}
            maxLength={LIMITE_TITULO_TAREFA}
            onChange={(event) => setTitulo(event.target.value)}
            placeholder="Protocolar petição"
          />
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="tarefa-descricao">Descrição</Label>
          <Textarea
            id="tarefa-descricao"
            value={descricao}
            maxLength={LIMITE_DESCRICAO}
            onChange={(event) => setDescricao(event.target.value)}
            placeholder="O que precisa ser feito"
            className="min-h-24"
          />
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="tarefa-responsavel">Responsável</Label>
          {pessoal ? (
            <Input id="tarefa-responsavel" value={usuario.name} readOnly />
          ) : (
            <Select value={responsavelId || undefined} onValueChange={setResponsavelId}>
              <SelectTrigger id="tarefa-responsavel" className="w-full">
                <SelectValue placeholder="Escolha um membro" />
              </SelectTrigger>
              <SelectContent>
                {membros.map((membro) => (
                  <SelectItem key={membro.id} value={membro.id}>
                    {membro.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="tarefa-processo">Processo</Label>
          {processoSelecionado ? (
            <div className="flex items-center justify-between gap-2 rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 py-2">
              <span className="min-w-0 truncate font-mono text-[13px] font-semibold text-[#111827]">
                {rotuloProcesso(processoSelecionado)}
              </span>
              <Button type="button" variant="ghost" size="sm" onClick={() => setProcessoId(null)}>
                Remover
              </Button>
            </div>
          ) : (
            <>
              <Input
                id="tarefa-processo"
                value={buscaProcesso}
                onChange={(event) => setBuscaProcesso(event.target.value)}
                placeholder="Busque por número ou parte"
              />
              {processosFiltrados.length > 0 ? (
                <ul className="max-h-36 overflow-y-auto rounded-lg border border-[#E5E7EB]">
                  {processosFiltrados.map((processo) => (
                    <li key={processo.id}>
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-left text-[13px] hover:bg-[#F8F9FC]"
                        onClick={() => {
                          setProcessoId(processo.id)
                          setBuscaProcesso('')
                        }}
                      >
                        <span className="block font-mono font-semibold text-[#111827]">
                          {formatarNumeroCnj(processo.nu_processo)}
                        </span>
                        <span className="block text-[#6B7280]">{partesDoProcesso(processo)}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[13px] text-[#9CA3AF]">
                  {processos.length === 0
                    ? 'Nenhum processo coletado para vincular.'
                    : 'Nenhum processo encontrado para essa busca.'}
                </p>
              )}
            </>
          )}
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="tarefa-prazo">Prazo</Label>
          <Input id="tarefa-prazo" type="date" value={prazo} onChange={(event) => setPrazo(event.target.value)} />
        </div>

        {erro ? <p className="text-sm text-[#B91C1C]">{erro}</p> : null}
      </div>

      <DialogFooter className="sm:justify-between">
        {tarefa ? (
          <Button
            type="button"
            variant="outline"
            disabled={salvando}
            onClick={() => {
              void excluir()
            }}
            className="border-[#FECACA] text-[#B91C1C] hover:bg-[#FEF2F2]"
          >
            {confirmarExclusao ? 'Confirmar exclusão' : 'Excluir'}
          </Button>
        ) : (
          <span />
        )}
        <div className="flex gap-2">
          <Button type="button" variant="outline" disabled={salvando} onClick={() => onAberto(false)}>
            Cancelar
          </Button>
          <Button type="button" disabled={salvando} onClick={() => void salvar()}>
            {salvando ? 'Salvando...' : 'Salvar'}
          </Button>
        </div>
      </DialogFooter>
    </>
  )
}

function responsavelPadrao(pessoal: boolean, usuario: AuthUser, membros: MemberPublic[]): string {
  if (pessoal) {
    return usuario.id
  }
  const proprio = membros.find((membro) => membro.email.toLowerCase() === usuario.email.toLowerCase())
  return proprio?.id ?? ''
}

function filtrarProcessos(processos: ProcessoLista[], busca: string): ProcessoLista[] {
  const termo = busca.trim().toLowerCase()
  const base = termo
    ? processos.filter((processo) => {
        const texto = [
          processo.nu_processo,
          processo.parte_ativa?.nome,
          processo.parte_passiva?.nome,
          processo.de_assunto,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        return texto.includes(termo)
      })
    : processos
  return base.slice(0, 8)
}

function rotuloProcesso(processo: ProcessoLista): string {
  return formatarNumeroCnj(processo.nu_processo)
}

function partesDoProcesso(processo: ProcessoLista): string {
  const partes = [processo.parte_ativa?.nome?.trim(), processo.parte_passiva?.nome?.trim()].filter(Boolean)
  return partes.join(' e ') || 'Partes não informadas'
}
