import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

const FATOS_EXTRAS_MAX = 8000

interface FatosExtrasPanelProps {
  valorInicial: string | null
  onSalvar: (texto: string | null) => void
  salvando: boolean
  desabilitado?: boolean
}

/**
 * Fatos, teses e argumentos que o e-SAJ não tem — o advogado digita aqui
 * para a IA usar ao redigir (ADR-016, Fase 2). Só salva quando o texto
 * muda (evita PATCH a cada tecla).
 */
export function FatosExtrasPanel({
  valorInicial,
  onSalvar,
  salvando,
  desabilitado = false,
}: FatosExtrasPanelProps) {
  const [texto, setTexto] = useState(valorInicial ?? '')
  const [alterado, setAlterado] = useState(false)

  useEffect(() => {
    setTexto(valorInicial ?? '')
    setAlterado(false)
  }, [valorInicial])

  return (
    <div>
      <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-2">
        Fatos e teses extras
      </p>
      <p className="text-[12px] text-[#6B7280] leading-snug mb-3">
        O e-SAJ não tem isso — descreva fatos, teses ou argumentos específicos que a IA deve
        considerar ao redigir a peça.
      </p>

      <textarea
        value={texto}
        onChange={(e) => {
          setTexto(e.target.value)
          setAlterado(true)
        }}
        maxLength={FATOS_EXTRAS_MAX}
        rows={5}
        disabled={desabilitado}
        placeholder="Ex.: O réu nunca foi notificado extrajudicialmente antes da propositura da ação..."
        className={`w-full resize-none rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] disabled:opacity-60 disabled:cursor-not-allowed ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      />

      <button
        type="button"
        disabled={desabilitado || salvando || !alterado}
        onClick={() => {
          onSalvar(texto.trim() ? texto.trim() : null)
          setAlterado(false)
        }}
        className="mt-2 w-full h-9 inline-flex items-center justify-center gap-1.5 rounded-lg bg-[#2563EB] text-[12px] font-semibold text-white hover:bg-[#1D4ED8] disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Save className="w-3.5 h-3.5" aria-hidden />
        {salvando ? 'Salvando…' : 'Salvar fatos'}
      </button>
    </div>
  )
}
