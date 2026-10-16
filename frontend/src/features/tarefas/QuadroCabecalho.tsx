import { useEffect, useState } from 'react'
import { Check, CheckSquare, Pencil } from 'lucide-react'

const LIMITE_TITULO = 80
const LIMITE_DESCRICAO = 280

interface QuadroCabecalhoProps {
  titulo: string
  descricao: string
  total: number
  podeEditar: boolean
  salvando: boolean
  onSalvar: (titulo: string, descricao: string) => Promise<void>
}

export function QuadroCabecalho({
  titulo,
  descricao,
  total,
  podeEditar,
  salvando,
  onSalvar,
}: QuadroCabecalhoProps) {
  const [editando, setEditando] = useState(false)
  const [nome, setNome] = useState(titulo)
  const [frase, setFrase] = useState(descricao)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!editando) {
      setNome(titulo)
      setFrase(descricao)
    }
  }, [titulo, descricao, editando])

  function cancelar() {
    setNome(titulo)
    setFrase(descricao)
    setErro(null)
    setEditando(false)
  }

  async function salvar() {
    const proximoNome = nome.trim()
    if (!proximoNome) {
      setErro('Dê um nome ao quadro.')
      return
    }
    setErro(null)
    try {
      await onSalvar(proximoNome, frase.trim())
      setEditando(false)
    } catch {
      setErro('Não foi possível salvar o quadro.')
    }
  }

  return (
    <section className="mb-4 rounded-2xl border border-[#E5E7EB] bg-white px-6 py-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 flex-1 gap-3">
          <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#EFF6FF] text-[#2563EB]">
            <CheckSquare className="h-5 w-5" aria-hidden />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold tracking-[0.18em] text-[#2563EB] uppercase">
              Quadro de tarefas
            </p>
            {editando ? (
              <div className="mt-1 grid gap-2">
                <input
                  value={nome}
                  maxLength={LIMITE_TITULO}
                  aria-label="Nome do quadro"
                  autoFocus
                  disabled={salvando}
                  onChange={(event) => setNome(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Escape') {
                      cancelar()
                    }
                  }}
                  className="h-9 w-full rounded-lg border border-[#E5E7EB] bg-white px-2 text-xl font-semibold text-[#111827]"
                />
                <textarea
                  value={frase}
                  maxLength={LIMITE_DESCRICAO}
                  aria-label="Descrição do quadro"
                  disabled={salvando}
                  rows={2}
                  onChange={(event) => setFrase(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Escape') {
                      cancelar()
                    }
                  }}
                  className="w-full resize-none rounded-lg border border-[#E5E7EB] bg-white px-2 py-1.5 text-sm text-[#6B7280]"
                />
                {erro ? <p className="text-sm text-[#B91C1C]">{erro}</p> : null}
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={salvando}
                    onClick={() => void salvar()}
                    className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#2563EB] px-3 text-[12px] font-semibold text-white disabled:opacity-60"
                  >
                    <Check className="h-3.5 w-3.5" aria-hidden />
                    {salvando ? 'Salvando...' : 'Salvar'}
                  </button>
                  <button
                    type="button"
                    disabled={salvando}
                    onClick={cancelar}
                    className="inline-flex h-8 items-center rounded-lg px-3 text-[12px] font-semibold text-[#6B7280] hover:bg-[#F3F4F6]"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            ) : podeEditar ? (
              <button
                type="button"
                onClick={() => setEditando(true)}
                className="group mt-0.5 block max-w-2xl rounded-lg text-left hover:bg-[#F8F9FC]"
              >
                <span className="flex items-center gap-2">
                  <span className="text-xl font-semibold text-[#111827]">{titulo}</span>
                  <Pencil
                    className="h-3.5 w-3.5 text-[#9CA3AF] opacity-0 group-hover:opacity-100"
                    aria-hidden
                  />
                </span>
                <span className="mt-1 block text-sm text-[#6B7280]">
                  {descricao || 'Adicione uma descrição para este quadro.'}
                </span>
              </button>
            ) : (
              <div className="mt-0.5">
                <h1 className="text-xl font-semibold text-[#111827]">{titulo}</h1>
                {descricao ? <p className="mt-1 max-w-2xl text-sm text-[#6B7280]">{descricao}</p> : null}
              </div>
            )}
          </div>
        </div>
        <span className="inline-flex h-9 items-center self-start rounded-full border border-[#E5E7EB] px-3 text-[12px] font-semibold text-[#374151]">
          {total} tarefa{total === 1 ? '' : 's'}
        </span>
      </div>
    </section>
  )
}
