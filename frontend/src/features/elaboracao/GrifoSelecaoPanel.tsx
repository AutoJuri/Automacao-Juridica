import { useState } from 'react'
import { Loader2, WandSparkles, X } from 'lucide-react'
import { ACOES_GRIFO } from './elaboracao.minuta'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

interface GrifoSelecaoPanelProps {
  trecho: string
  top: number | null
  bottom: number | null
  left: number
  onFechar: () => void
  onExecutar: (instrucao: string) => void
  executando: boolean
  erro: string | null
}

export function GrifoSelecaoPanel({
  trecho,
  top,
  bottom,
  left,
  onFechar,
  onExecutar,
  executando,
  erro,
}: GrifoSelecaoPanelProps) {
  const [prompt, setPrompt] = useState('')
  const [validacao, setValidacao] = useState<string | null>(null)
  const preview = trecho.trim().length > 160 ? `${trecho.trim().slice(0, 160)}…` : trecho.trim()

  function executar() {
    const instrucao = prompt.trim()
    if (!instrucao) {
      setValidacao('Descreva o que a IA deve fazer com este trecho.')
      return
    }
    setValidacao(null)
    onExecutar(instrucao)
  }

  return (
    <div
      className="fixed z-50 w-[min(28rem,calc(100vw-2rem))] rounded-xl border border-[#E5E7EB] bg-white shadow-xl p-4"
      style={{
        top: top ?? 'auto',
        bottom: bottom ?? 'auto',
        left,
        maxHeight: bottom != null ? `calc(100vh - ${bottom}px - 8px)` : undefined,
      }}
      role="dialog"
      aria-label="Editar trecho selecionado"
      onMouseDown={(e) => {
        if ((e.target as HTMLElement).closest('textarea')) {
          return
        }
        e.preventDefault()
      }}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <p className="text-[11px] font-semibold text-[#2563EB] tracking-[0.14em] uppercase">
            Editar trecho selecionado
          </p>
          <p className="text-[13px] text-[#6B7280] mt-1 leading-snug italic">“{preview || '…'}”</p>
        </div>
        <button
          type="button"
          onClick={onFechar}
          className="h-7 w-7 inline-flex items-center justify-center rounded-md text-[#6B7280] hover:bg-[#F3F4F6]"
          aria-label="Fechar"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {ACOES_GRIFO.map((acao) => (
          <button
            key={acao.id}
            type="button"
            onClick={() => {
              setPrompt(acao.rotulo)
              setValidacao(null)
            }}
            className="h-7 px-2.5 rounded-md border border-[#BFDBFE] bg-[#EFF6FF] text-[12px] font-semibold text-[#1D4ED8] hover:bg-[#DBEAFE]"
          >
            {acao.rotulo}
          </button>
        ))}
      </div>

      <textarea
        value={prompt}
        onChange={(e) => {
          setPrompt(e.target.value)
          setValidacao(null)
        }}
        rows={2}
        disabled={executando}
        placeholder="Ex: Como deseja reescrever este trecho específico?"
        className={`w-full resize-none rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-3 py-2 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] disabled:opacity-60 ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      />

      <button
        type="button"
        onClick={executar}
        disabled={executando}
        className="mt-3 w-full h-10 inline-flex items-center justify-center gap-2 rounded-lg bg-[#2563EB] text-white text-[13px] font-semibold disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {executando ? (
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
        ) : (
          <WandSparkles className="w-4 h-4" aria-hidden />
        )}
        {executando ? 'Executando…' : 'Executar alteração no grifo'}
      </button>

      {validacao ? (
        <p className="mt-2 text-[12px] text-[#92400E] bg-[#FFFBEB] border border-[#FDE68A] rounded-md px-2.5 py-2 leading-snug">
          {validacao}
        </p>
      ) : null}

      {erro ? (
        <p className="mt-2 text-[12px] text-[#B91C1C] bg-[#FEF2F2] border border-[#FECACA] rounded-md px-2.5 py-2 leading-snug">
          {erro}
        </p>
      ) : null}
    </div>
  )
}
