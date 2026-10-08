import { useState } from 'react'
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { Plus } from 'lucide-react'

import { MAX_COLUNAS, moverTarefa } from './tarefas.board'
import { KanbanColuna } from './KanbanColuna'
import { TarefaCardOverlay } from './TarefaCard'
import type { Quadro, Tarefa } from './tarefas.types'

interface KanbanBoardProps {
  quadro: Quadro
  podeConfigurar: boolean
  onMover: (quadro: Quadro, tarefaId: string) => void
  onAdicionarColuna: () => void
  nomeResponsavel: (responsavelId: string) => string
  rotuloProcesso: (processoId: string | null) => string | null
  onRenomear: (colunaId: string, titulo: string) => void
  onRemover: (colunaId: string) => void
  onMarcarConclusao: (colunaId: string) => void
  onNovaTarefa: (colunaId: string) => void
  onAbrirTarefa: (tarefa: Tarefa) => void
  onEditarTarefa: (tarefa: Tarefa) => void
  onExcluirTarefa: (tarefaId: string) => void
  onCarregarMais: (colunaId: string) => void
  carregandoMais: boolean
}

export function KanbanBoard({
  quadro,
  podeConfigurar,
  onMover,
  onAdicionarColuna,
  nomeResponsavel,
  rotuloProcesso,
  onRenomear,
  onRemover,
  onMarcarConclusao,
  onNovaTarefa,
  onAbrirTarefa,
  onEditarTarefa,
  onExcluirTarefa,
  onCarregarMais,
  carregandoMais,
}: KanbanBoardProps) {
  const [ativaId, setAtivaId] = useState<string | null>(null)
  const sensores = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )
  const ativa = quadro.tarefas.find((tarefa) => tarefa.id === ativaId) ?? null
  const noLimite = quadro.colunas.length >= MAX_COLUNAS

  function aoIniciar(event: DragStartEvent) {
    setAtivaId(String(event.active.id))
  }

  function aoTerminar(event: DragEndEvent) {
    setAtivaId(null)
    const sobreId = event.over ? String(event.over.id) : ''
    if (!sobreId) {
      return
    }
    const tarefaId = String(event.active.id)
    const proximo = moverTarefa(quadro, tarefaId, sobreId)
    if (proximo !== quadro) {
      onMover(proximo, tarefaId)
    }
  }

  return (
    <DndContext
      sensors={sensores}
      collisionDetection={closestCorners}
      onDragStart={aoIniciar}
      onDragEnd={aoTerminar}
      onDragCancel={() => setAtivaId(null)}
    >
      <div className="flex min-h-0 flex-1 gap-4 overflow-x-auto pb-2">
        {quadro.colunas.map((coluna) => (
          <KanbanColuna
            key={coluna.id}
            coluna={coluna}
            quadro={quadro}
            nomeResponsavel={nomeResponsavel}
            rotuloProcesso={rotuloProcesso}
            podeConfigurar={podeConfigurar}
            onRenomear={onRenomear}
            onRemover={onRemover}
            onMarcarConclusao={onMarcarConclusao}
            onNovaTarefa={onNovaTarefa}
            onAbrirTarefa={onAbrirTarefa}
            onEditarTarefa={onEditarTarefa}
            onExcluirTarefa={onExcluirTarefa}
            onMover={onMover}
            onCarregarMais={onCarregarMais}
            carregandoMais={carregandoMais}
          />
        ))}
        {podeConfigurar && !noLimite ? (
          <button
            type="button"
            title="Adicionar coluna"
            onClick={onAdicionarColuna}
            className="inline-flex h-12 w-[280px] shrink-0 items-center justify-center gap-1.5 self-start rounded-2xl border border-dashed border-[#D1D5DB] bg-white text-[13px] font-semibold text-[#2563EB] hover:border-[#2563EB]"
          >
            <Plus className="h-3.5 w-3.5" aria-hidden />
            Adicionar coluna
          </button>
        ) : null}
      </div>
      <DragOverlay>
        {ativa ? (
          <TarefaCardOverlay
            tarefa={ativa}
            responsavelNome={ativa.responsavelNome || nomeResponsavel(ativa.responsavelId)}
            processoRotulo={rotuloProcesso(ativa.processoId)}
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}
