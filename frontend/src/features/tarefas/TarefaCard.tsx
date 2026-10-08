import { useEffect, useRef, useState } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ArrowRight, Calendar, CircleCheck, GripVertical, Pencil, Trash2 } from 'lucide-react'

import { estaAtrasada, type AtalhoColuna, type TomDaColuna } from './tarefas.board'
import { CORES_COLUNA } from './tarefas.cores'
import { ResponsavelAvatar } from './ResponsavelAvatar'
import type { Tarefa } from './tarefas.types'
import { formatarPrazo, trecho } from './tarefas.texto'

export interface TarefaCardDados {
  tarefa: Tarefa
  responsavelNome: string
  processoRotulo: string | null
  tom: TomDaColuna
  avancarPara: AtalhoColuna | null
  concluirPara: AtalhoColuna | null
  onAbrir: (tarefa: Tarefa) => void
  onEditar: (tarefa: Tarefa) => void
  onExcluir: (tarefaId: string) => void
  onMoverPara: (tarefaId: string, colunaId: string) => void
}

export function TarefaCard({
  tarefa,
  responsavelNome,
  processoRotulo,
  tom,
  avancarPara,
  concluirPara,
  onAbrir,
  onEditar,
  onExcluir,
  onMoverPara,
}: TarefaCardDados) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: tarefa.id,
  })
  const arrastou = useRef(false)
  const [confirmarExclusao, setConfirmarExclusao] = useState(false)
  const atrasada = !tarefa.concluida && estaAtrasada(tarefa.prazo)

  useEffect(() => {
    if (isDragging) {
      arrastou.current = true
    }
  }, [isDragging])

  return (
    <article
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={[
        'relative overflow-hidden rounded-xl border bg-white shadow-sm',
        isDragging ? 'border-[#2563EB] opacity-40' : atrasada ? 'border-[#FECACA]' : 'border-[#E5E7EB]',
      ].join(' ')}
    >
      <div
        className="cursor-pointer px-3 py-3 pr-16 active:cursor-grabbing"
        {...attributes}
        {...listeners}
        onClick={() => {
          if (arrastou.current) {
            arrastou.current = false
            return
          }
          setConfirmarExclusao(false)
          onAbrir(tarefa)
        }}
      >
        <TarefaCardCorpo
          tarefa={tarefa}
          responsavelNome={responsavelNome}
          processoRotulo={processoRotulo}
          atrasada={atrasada}
        />
      </div>
      <span aria-hidden className={['absolute inset-y-0 left-0 w-1', CORES_COLUNA[tom].faixa].join(' ')} />
      <div className="absolute top-2 right-2 flex items-center gap-0.5">
        <button
          type="button"
          aria-label={confirmarExclusao ? `Confirmar exclusão de ${tarefa.titulo}` : `Excluir ${tarefa.titulo}`}
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => {
            event.stopPropagation()
            if (!confirmarExclusao) {
              setConfirmarExclusao(true)
              return
            }
            setConfirmarExclusao(false)
            onExcluir(tarefa.id)
          }}
          className={[
            'inline-flex h-7 items-center justify-center rounded-lg hover:bg-[#FEF2F2]',
            confirmarExclusao ? 'px-1.5 text-[11px] font-semibold text-[#B91C1C]' : 'w-7 text-[#9CA3AF] hover:text-[#B91C1C]',
          ].join(' ')}
        >
          {confirmarExclusao ? 'Excluir?' : <Trash2 className="h-3.5 w-3.5" aria-hidden />}
        </button>
        <button
          type="button"
          aria-label={`Editar ${tarefa.titulo}`}
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => {
            event.stopPropagation()
            setConfirmarExclusao(false)
            onEditar(tarefa)
          }}
          className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]"
        >
          <Pencil className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>
      {avancarPara || concluirPara ? (
        <div className="flex items-center gap-1 border-t border-[#F3F4F6] px-2 py-1.5">
          {avancarPara ? (
            <button
              type="button"
              aria-label={`Mover ${tarefa.titulo} para ${avancarPara.titulo}`}
              title={`Mover para ${avancarPara.titulo}`}
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation()
                onMoverPara(tarefa.id, avancarPara.id)
              }}
              className={[
                'inline-flex h-7 min-w-0 flex-1 items-center gap-1 rounded-lg px-1.5 text-[12px] font-semibold',
                CORES_COLUNA.andamento.botao,
              ].join(' ')}
            >
              <ArrowRight className="h-3.5 w-3.5 shrink-0" aria-hidden />
              <span className="truncate">{avancarPara.titulo}</span>
            </button>
          ) : (
            <span />
          )}
          {concluirPara ? (
            <button
              type="button"
              aria-label={`Concluir ${tarefa.titulo}`}
              title={`Mover para ${concluirPara.titulo}`}
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation()
                onMoverPara(tarefa.id, concluirPara.id)
              }}
              className={[
                'inline-flex h-7 shrink-0 items-center gap-1 rounded-lg px-1.5 text-[12px] font-semibold',
                CORES_COLUNA.conclusao.botao,
              ].join(' ')}
            >
              <CircleCheck className="h-3.5 w-3.5" aria-hidden />
              Concluir
            </button>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

export function TarefaCardOverlay({
  tarefa,
  responsavelNome,
  processoRotulo,
}: Pick<TarefaCardDados, 'tarefa' | 'responsavelNome' | 'processoRotulo'>) {
  return (
    <article className="w-[340px] rounded-xl border border-[#2563EB] bg-white px-3 py-3 shadow-sm">
      <TarefaCardCorpo
        tarefa={tarefa}
        responsavelNome={responsavelNome}
        processoRotulo={processoRotulo}
        atrasada={!tarefa.concluida && estaAtrasada(tarefa.prazo)}
      />
    </article>
  )
}

function TarefaCardCorpo({
  tarefa,
  responsavelNome,
  processoRotulo,
  atrasada,
}: Pick<TarefaCardDados, 'tarefa' | 'responsavelNome' | 'processoRotulo'> & { atrasada: boolean }) {
  const descricao = trecho(tarefa.descricao)

  return (
    <div className="min-w-0">
      <div className="flex items-start gap-2">
        <GripVertical className="mt-0.5 h-4 w-4 shrink-0 text-[#9CA3AF]" aria-hidden />
        <p className="text-sm font-semibold text-[#111827]">{tarefa.titulo}</p>
      </div>
      {descricao ? <p className="mt-1 pl-6 text-[13px] text-[#6B7280]">{descricao}</p> : null}
      {processoRotulo ? (
        <p className="mt-2 pl-6 font-mono text-[12px] font-semibold text-[#374151]">{processoRotulo}</p>
      ) : null}
      <div className="mt-3 flex items-center justify-between gap-2 pl-6">
        {tarefa.prazo ? (
          <span
            className={[
              'inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[12px] font-medium',
              atrasada ? 'bg-[#FEF2F2] text-[#B91C1C]' : 'text-[#6B7280]',
            ].join(' ')}
          >
            <Calendar className="h-3.5 w-3.5" aria-hidden />
            {formatarPrazo(tarefa.prazo)}
            {atrasada ? <span>Vencida</span> : null}
          </span>
        ) : (
          <span />
        )}
        <ResponsavelAvatar nome={responsavelNome} />
      </div>
    </div>
  )
}
