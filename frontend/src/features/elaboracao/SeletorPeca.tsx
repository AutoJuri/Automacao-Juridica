import { FileText } from 'lucide-react'
import { modelosPeca, type ModeloPeca } from './elaboracao.mock'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

interface SeletorPecaProps {
  pecaSelecionada: string
  onChange: (id: string) => void
}

const grupos = [...new Set(modelosPeca.map((m) => m.grupo))]

function getPecaById(id: string): ModeloPeca | undefined {
  return modelosPeca.find((m) => m.id === id)
}

export function SeletorPeca({ pecaSelecionada, onChange }: SeletorPecaProps) {
  const peca = getPecaById(pecaSelecionada)

  return (
    <div>
      <p className="text-[10px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-1">
        Seletor de peça
      </p>
      <p className="text-[10px] font-semibold text-[#2563EB] tracking-[0.12em] uppercase mb-2">
        Sugerido por IA
      </p>
      <div className="relative">
        <div className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2">
          <FileText className="w-3.5 h-3.5 text-[#9CA3AF]" />
        </div>
        <select
          value={pecaSelecionada}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full appearance-none bg-white border border-[#E5E7EB] rounded-lg pl-8 pr-8 py-2 text-[13px] text-[#111827] font-medium cursor-pointer ${FOCO_CAMPO}`}
          {...propsFocoCampo}
        >
          {grupos.map((grupo) => (
            <optgroup key={grupo} label={grupo}>
              {modelosPeca
                .filter((m) => m.grupo === grupo)
                .map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nome}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>
        <div className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[#9CA3AF]">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 4L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
      {peca && (
        <p className="mt-1 text-[10px] text-[#9CA3AF]">{peca.grupo}</p>
      )}
    </div>
  )
}
