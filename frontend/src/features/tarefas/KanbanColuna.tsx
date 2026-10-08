import { useEffect, useState } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CircleCheck, Plus, Trash2 } from 'lucide-react'

import { atalhosDaColuna, idDropColuna, moverTarefa, tarefasDaColuna, tomDaColuna } from './tarefas.board'
import { CORES_COLUNA } from './tarefas.cores'
import { TarefaCard } from './TarefaCard'
import type { Coluna, Quadro, Tarefa } from './tarefas.types'

interface KanbanColunaProps {
  coluna: Coluna
  quadro: Quadro
  podeConfigurar: boolean
  nomeResponsavel: (responsavelId: string) => string
  rotuloProcesso: (processoId: string | null) => string | null
  onRenomear: (colunaId: string, titulo: string) => void
  onRemover: (colunaId: string) => void
  onMarcarConclusao: (colunaId: string) => void
  onNovaTarefa: (colunaId: string) => void
  onAbrirTarefa: (tarefa: Tarefa) => void
  onEditarTarefa: (tarefa: Tarefa) => void
  onExcluirTarefa: (tarefaId: string) => void
  onMover: (quadro: Quadro, tarefaId: string) => void
  onCarregarMais: (colunaId: string) => void
  carregandoMais: boolean
}

export function KanbanColuna({
  coluna,
  quadro,
  podeConfigurar,
  nomeResponsavel,
  rotuloProcesso,
  onRenomear,
  onRemover,
  onMarcarConclusao,
  onNovaTarefa,
  onAbrirTarefa,
  onEditarTarefa,
  onExcluirTarefa,
  onMover,
  onCarregarMais,
  carregandoMais,
}: KanbanColunaProps) {
  const tarefas = tarefasDaColuna(quadro, coluna.id)
  const tom = tomDaColuna(quadro.colunas, coluna)
  const cores = CORES_COLUNA[tom]
  const atalhos = atalhosDaColuna(quadro, coluna.id)
  const podeRemover = podeConfigurar && quadro.colunas.length > 1 && tarefas.length === 0
  const { setNodeRef, isOver } = useDroppable({ id: idDropColuna(coluna.id) })
  const [editando, setEditando] = useState(false)
  const [titulo, setTitulo] = useState(coluna.titulo)

  useEffect(() => {
    setTitulo(coluna.titulo)
  }, [coluna.titulo])

  function confirmarTitulo() {
    setEditando(false)
    if (!titulo.trim()) {
      setTitulo(coluna.titulo)
      return
    }
    onRenomear(coluna.id, titulo)
  }

  function moverPara(tarefaId: string, colunaId: string) {
    const proximo = moverTarefa(quadro, tarefaId, idDropColuna(colunaId))
    if (proximo !== quadro) {
      onMover(proximo, tarefaId)
    }
  }

  return (
    <section
      className={[
        'flex min-h-0 w-0 min-w-0 flex-1 basis-0 flex-col rounded-2xl border',
        cores.fundo,
        isOver ? 'border-[#2563EB]' : cores.borda,
      ].join(' ')}
      aria-label={coluna.titulo}
    >
      <header className="flex items-center gap-2 px-3 py-3">
        <span aria-hidden className={['h-2 w-2 shrink-0 rounded-full', cores.ponto].join(' ')} />
        {editando ? (
          <input
            value={titulo}
            maxLength={40}
            aria-label="Nome da coluna"
            autoFocus
            onChange={(event) => setTitulo(event.target.value)}
            onBlur={confirmarTitulo}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.currentTarget.blur()
              }
              if (event.key === 'Escape') {
                setTitulo(coluna.titulo)
                setEditando(false)
              }
            }}
            className="h-8 min-w-0 flex-1 rounded-lg border border-[#E5E7EB] bg-white px-2 text-sm font-semibold text-[#111827]"
          />
        ) : podeConfigurar ? (
          <button
            type="button"
            className={['min-w-0 flex-1 truncate text-left text-sm font-semibold', cores.texto].join(' ')}
            onClick={() => setEditando(true)}
          >
            {coluna.titulo}
          </button>
        ) : (
          <p className={['min-w-0 flex-1 truncate text-sm font-semibold', cores.texto].join(' ')}>
            {coluna.titulo}
          </p>
        )}
        <span
          className={[
            'inline-flex h-6 min-w-6 items-center justify-center rounded-full px-1.5 text-[12px] font-semibold',
            cores.badge,
          ].join(' ')}
        >
          {coluna.total}
        </span>
        {coluna.conclusao ? (
          <span className={['inline-flex items-center gap-1 text-[11px] font-semibold', cores.texto].join(' ')}>
            <CircleCheck className="h-3.5 w-3.5" aria-hidden />
            Conclusão
          </span>
        ) : podeConfigurar ? (
          <button
            type="button"
            aria-label={`Definir ${coluna.titulo} como coluna de conclusão`}
            title="Coluna de conclusão"
            onClick={() => onMarcarConclusao(coluna.id)}
            className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-[#9CA3AF] hover:bg-white hover:text-[#2563EB]"
          >
            <CircleCheck className="h-3.5 w-3.5" aria-hidden />
          </button>
        ) : null}
        {podeRemover ? (
          <button
            type="button"
            aria-label={`Remover coluna ${coluna.titulo}`}
            onClick={() => onRemover(coluna.id)}
            className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-[#9CA3AF] hover:bg-white hover:text-[#B91C1C]"
          >
            <Trash2 className="h-3.5 w-3.5" aria-hidden />
          </button>
        ) : null}
      </header>

      <div ref={setNodeRef} className="flex min-h-[140px] flex-1 flex-col gap-2 overflow-y-auto px-3 pb-2">
        <SortableContext items={tarefas.map((tarefa) => tarefa.id)} strategy={verticalListSortingStrategy}>
          {tarefas.length === 0 ? (
            <p className="px-1 py-6 text-center text-[13px] text-[#9CA3AF]">
              {quadro.tarefas.length === 0 && quadro.colunas[0]?.id === coluna.id
                ? 'Crie a primeira tarefa nesta coluna.'
                : 'Arraste uma tarefa para cá.'}
            </p>
          ) : (
            tarefas.map((tarefa) => (
              <TarefaCard
                key={tarefa.id}
                tarefa={tarefa}
                responsavelNome={tarefa.responsavelNome || nomeResponsavel(tarefa.responsavelId)}
                processoRotulo={rotuloProcesso(tarefa.processoId)}
                tom={tom}
                avancarPara={atalhos.avancar}
                concluirPara={atalhos.concluir}
                onAbrir={onAbrirTarefa}
                onEditar={onEditarTarefa}
                onExcluir={onExcluirTarefa}
                onMoverPara={moverPara}
              />
            ))
          )}
        </SortableContext>
      </div>

      {coluna.conclusao && tarefas.length < coluna.total ? (
        <div className="px-3 pb-1">
          <button
            type="button"
            disabled={carregandoMais}
            onClick={() => onCarregarMais(coluna.id)}
            className={[
              'inline-flex h-9 w-full items-center justify-center rounded-lg border bg-white text-[13px] font-semibold disabled:opacity-60',
              cores.texto,
              cores.borda,
            ].join(' ')}
          >
            {carregandoMais ? 'Carregando…' : 'Carregar mais'}
          </button>
        </div>
      ) : null}

      <div className="p-3 pt-1">
        <button
          type="button"
          onClick={() => onNovaTarefa(coluna.id)}
          className="inline-flex h-9 w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-[#D1D5DB] bg-white text-[13px] font-semibold text-[#2563EB] hover:border-[#2563EB]"
        >
          <Plus className="h-3.5 w-3.5" aria-hidden />
          Nova tarefa
        </button>
      </div>
    </section>
  )
}
