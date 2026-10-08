import { useState, type ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import { Calendar, Pencil, Trash2 } from 'lucide-react'

import { Button } from '#/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '#/components/ui/dialog'
import { mensagemDeErro } from '#/features/auth/auth.errors'

import type { Tarefa } from './tarefas.types'
import { estaAtrasada } from './tarefas.board'
import { formatarPrazo } from './tarefas.texto'

interface TarefaDetalheDialogProps {
  tarefa: Tarefa | null
  colunaNome: string
  responsavelNome: string
  processoRotulo: string | null
  onAberto: (aberto: boolean) => void
  onEditar: (tarefa: Tarefa) => void
  onExcluir: (tarefaId: string) => Promise<void>
}

export function TarefaDetalheDialog({
  tarefa,
  colunaNome,
  responsavelNome,
  processoRotulo,
  onAberto,
  onEditar,
  onExcluir,
}: TarefaDetalheDialogProps) {
  const [confirmar, setConfirmar] = useState(false)
  const [excluindo, setExcluindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const atrasada = Boolean(tarefa && !tarefa.concluida && estaAtrasada(tarefa.prazo))

  async function excluir() {
    if (!tarefa) {
      return
    }
    if (!confirmar) {
      setConfirmar(true)
      return
    }
    setExcluindo(true)
    setErro(null)
    try {
      await onExcluir(tarefa.id)
      onAberto(false)
    } catch (falha) {
      setConfirmar(false)
      setErro(
        mensagemDeErro(falha, {
          403: 'Sem permissão para excluir esta tarefa.',
          404: 'Essa tarefa não está mais no quadro.',
        }),
      )
    } finally {
      setExcluindo(false)
    }
  }

  return (
    <Dialog
      open={tarefa !== null}
      onOpenChange={(aberto) => {
        if (!aberto) {
          setConfirmar(false)
          setErro(null)
          onAberto(false)
        }
      }}
    >
      <DialogContent className="sm:max-w-lg">
        {tarefa ? (
          <>
            <DialogHeader>
              <DialogTitle>{tarefa.titulo}</DialogTitle>
              <DialogDescription>
                {tarefa.concluida ? 'Tarefa concluída' : 'Tarefa em aberto'}
                {colunaNome ? ` · ${colunaNome}` : ''}
              </DialogDescription>
            </DialogHeader>

            <dl className="grid gap-4">
              <Campo rotulo="Descrição">
                {tarefa.descricao.trim() ? (
                  <p className="text-sm whitespace-pre-wrap text-[#111827]">{tarefa.descricao}</p>
                ) : (
                  <p className="text-sm text-[#9CA3AF] italic">Sem descrição.</p>
                )}
              </Campo>
              <div className="grid gap-4 sm:grid-cols-2">
                <Campo rotulo="Responsável">
                  <p className="text-sm text-[#111827]">{responsavelNome}</p>
                </Campo>
                <Campo rotulo="Coluna">
                  <p className="text-sm text-[#111827]">{colunaNome || 'Sem coluna'}</p>
                </Campo>
                <Campo rotulo="Processo">
                  {tarefa.processoId && processoRotulo ? (
                    <Link
                      to="/"
                      search={{ processo: tarefa.processoId }}
                      className="font-mono text-sm font-semibold text-[#2563EB] underline-offset-2 hover:underline"
                    >
                      {processoRotulo}
                    </Link>
                  ) : (
                    <p className="text-sm text-[#9CA3AF] italic">Nenhum processo vinculado</p>
                  )}
                </Campo>
                <Campo rotulo="Prazo">
                  {tarefa.prazo ? (
                    <p
                      className={[
                        'inline-flex items-center gap-1 text-sm',
                        atrasada ? 'font-semibold text-[#B91C1C]' : 'text-[#111827]',
                      ].join(' ')}
                    >
                      <Calendar className="h-3.5 w-3.5" aria-hidden />
                      {formatarPrazo(tarefa.prazo)}
                      {atrasada ? ' · Vencida' : ''}
                    </p>
                  ) : (
                    <p className="text-sm text-[#9CA3AF] italic">Sem prazo.</p>
                  )}
                </Campo>
                {tarefa.criadorNome ? (
                  <Campo rotulo="Criada por">
                    <p className="text-sm text-[#111827]">{tarefa.criadorNome}</p>
                  </Campo>
                ) : null}
              </div>
            </dl>

            {erro ? <p className="text-sm text-[#B91C1C]">{erro}</p> : null}

            <DialogFooter className="sm:justify-between">
              <Button
                type="button"
                variant="outline"
                disabled={excluindo}
                onClick={() => void excluir()}
                className="border-[#FECACA] bg-white text-[#B91C1C] hover:bg-[#FEF2F2]"
              >
                <Trash2 className="h-3.5 w-3.5" aria-hidden />
                {confirmar ? 'Confirmar exclusão' : 'Excluir'}
              </Button>
              <Button
                type="button"
                disabled={excluindo}
                onClick={() => {
                  onEditar(tarefa)
                }}
              >
                <Pencil className="h-3.5 w-3.5" aria-hidden />
                Editar
              </Button>
            </DialogFooter>
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function Campo({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  return (
    <div>
      <dt className="mb-1 text-[11px] font-semibold tracking-[0.14em] text-[#9CA3AF] uppercase">{rotulo}</dt>
      <dd>{children}</dd>
    </div>
  )
}
