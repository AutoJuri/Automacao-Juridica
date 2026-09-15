import { useMemo, useState } from 'react'
import { Search, Upload } from 'lucide-react'
import { Input } from '#/components/ui/input'
import { JULGADOS_ILUSTRATIVOS, type JulgadoIlustrativo } from './elaboracao.mock'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

type AbaJuris = 'todos' | JulgadoIlustrativo['categoria'] | 'autores'

const ABAS: { id: AbaJuris; label: string }[] = [
  { id: 'todos', label: 'Todos' },
  { id: 'tribunais', label: 'Tribunais' },
  { id: 'decisoes', label: 'Decisões' },
  { id: 'sumulas', label: 'Súmulas' },
  { id: 'leis', label: 'Leis' },
  { id: 'autores', label: 'Autores' },
]

export function JurisprudenciaPanel() {
  const [busca, setBusca] = useState('')
  const [aba, setAba] = useState<AbaJuris>('todos')
  const [marcados, setMarcados] = useState<Record<string, boolean>>({})

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return JULGADOS_ILUSTRATIVOS.filter((item) => {
      if (aba === 'autores' || (aba !== 'todos' && item.categoria !== aba)) {
        return false
      }
      if (!termo) {
        return true
      }
      return `${item.titulo} ${item.tribunal} ${item.resumo}`.toLowerCase().includes(termo)
    })
  }, [busca, aba])

  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-2">
        <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase">
          Jurisprudências a usar
        </p>
        <span className="text-[11px] font-semibold text-[#2563EB]">
          {Object.values(marcados).filter(Boolean).length} selecionadas
        </span>
      </div>
      <p className="text-[11px] text-[#B45309] bg-[#FFFBEB] border border-[#FDE68A] rounded-md px-2.5 py-1.5 mb-3 leading-snug">
        Julgados ilustrativos — não vêm do e-SAJ.
      </p>

      <div className="relative mb-2">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#9CA3AF]" />
        <Input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por julgado, STJ, STF..."
          className={`pl-8 h-8 text-[12px] border-[#E5E7EB] bg-[#F8F9FC] shadow-none ${FOCO_CAMPO}`}
          {...propsFocoCampo}
        />
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {ABAS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setAba(item.id)}
            className={[
              'h-6 px-2 rounded-md text-[10px] font-semibold',
              aba === item.id
                ? 'bg-[#2563EB] text-white'
                : 'bg-[#F3F4F6] text-[#4B5563] hover:bg-[#E5E7EB]',
            ].join(' ')}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="space-y-2 max-h-[240px] overflow-y-auto pr-0.5">
        {filtrados.length === 0 ? (
          <p className="text-[12px] text-[#9CA3AF] px-0.5">Nenhum julgado ilustrativo nesta aba.</p>
        ) : (
          filtrados.map((item) => (
          <label
            key={item.id}
            className="flex gap-2 rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-2.5 py-2 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={Boolean(marcados[item.id])}
              onChange={(e) =>
                setMarcados((prev) => ({ ...prev, [item.id]: e.target.checked }))
              }
              className="mt-0.5 accent-[#2563EB]"
            />
            <span className="min-w-0">
              <span className="flex items-center gap-1.5">
                <span className="text-[13px] font-semibold text-[#111827] leading-snug">
                  {item.titulo}
                </span>
                <span className="text-[10px] font-semibold text-[#2563EB] bg-[#EFF6FF] px-1.5 py-0.5 rounded shrink-0">
                  {item.tribunal}
                </span>
              </span>
              <span className="block text-[12px] text-[#6B7280] mt-0.5 leading-snug">
                {item.resumo}
              </span>
            </span>
          </label>
          ))
        )}
      </div>

      <button
        type="button"
        disabled
        title="Upload de tese ainda não está em operação"
        className="mt-3 w-full h-9 inline-flex items-center justify-center gap-1.5 rounded-lg bg-[#2563EB] text-[12px] font-semibold text-white opacity-50"
      >
        <Upload className="w-3.5 h-3.5" />
        Enviar tese / jurisprudência
      </button>
    </div>
  )
}
