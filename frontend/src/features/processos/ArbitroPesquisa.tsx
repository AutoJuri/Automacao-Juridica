import { Search } from 'lucide-react'
import { Input } from '#/components/ui/input'
import { portaisDisponiveis, type PortalKey } from './portais.mock'

interface ArbitroPesquisaProps {
  searchQuery: string
  onSearchQueryChange: (value: string) => void
  portalSelecionado: PortalKey
  onPortalChange: (value: PortalKey) => void
}

export function ArbitroPesquisa({
  searchQuery,
  onSearchQueryChange,
  portalSelecionado,
  onPortalChange,
}: ArbitroPesquisaProps) {
  return (
    <div className="relative z-10 shrink-0 rounded-xl border border-[#E5E7EB] bg-white px-6 py-5 shadow-sm">
      <p className="text-[10px] font-semibold text-[#3B5BDB] tracking-[0.2em] uppercase mb-1">
        Árbitro de Pesquisa
      </p>
      <h1 className="text-xl font-semibold text-[#111827] mb-4">
        Consulta Unificada de Autos Legistas
      </h1>
      <div className="flex gap-3">
        <div className="relative flex-1 min-w-0">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF] pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            placeholder="Pesquise por número do processo, cliente autor ou tribunal..."
            className="pl-10 h-11 text-sm border-[#E5E7EB] bg-[#F8F9FC] text-[#111827] placeholder:text-[#9CA3AF] focus-visible:ring-[#3B5BDB] focus-visible:border-[#3B5BDB] rounded-lg"
          />
        </div>

        <div className="relative shrink-0">
          <label htmlFor="portal-select" className="sr-only">
            Filtrar por portal
          </label>
          <select
            id="portal-select"
            value={portalSelecionado}
            onChange={(e) => onPortalChange(e.target.value as PortalKey)}
            className="h-11 w-[180px] appearance-none rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-4 pr-9 text-sm text-[#374151] cursor-pointer outline-none transition-colors hover:bg-white focus:border-[#3B5BDB] focus:ring-2 focus:ring-[#3B5BDB]/20"
          >
            {portaisDisponiveis.map((portal) => (
              <option key={portal.value} value={portal.value}>
                {portal.label}
              </option>
            ))}
          </select>
          <span
            aria-hidden
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] text-xs"
          >
            ▾
          </span>
        </div>
      </div>
    </div>
  )
}
