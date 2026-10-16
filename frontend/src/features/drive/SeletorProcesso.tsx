import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, X } from 'lucide-react'

import { PROCESSOS_QUERY_KEY } from '#/features/processos/processos.constants'
import { listarProcessos } from '#/features/processos/processos.api'
import { formatarNumeroCnj } from '#/features/processos/processos.format'

import type { PastaProcesso } from './drive.types'

const RESULTADOS_VISIVEIS = 6

interface SeletorProcessoProps {
  selecionado: PastaProcesso | null
  onChange: (processo: PastaProcesso | null) => void
}

function nomeDaParte(parte: { nome?: string | null } | null | undefined): string | null {
  const nome = parte?.nome?.trim()
  return nome ? nome : null
}

/** Vínculo opcional: busca nos processos do próprio usuário. */
export function SeletorProcesso({ selecionado, onChange }: SeletorProcessoProps) {
  const [texto, setTexto] = useState('')
  const [busca, setBusca] = useState('')

  useEffect(() => {
    const id = window.setTimeout(() => setBusca(texto.trim()), 300)
    return () => window.clearTimeout(id)
  }, [texto])

  const resultados = useQuery({
    queryKey: [...PROCESSOS_QUERY_KEY, 'vinculo-drive', busca],
    queryFn: () => listarProcessos(busca),
    enabled: selecionado === null,
  })

  if (selecionado) {
    const polos = [selecionado.autor, selecionado.reu].filter(Boolean).join(' × ')
    return (
      <div className="flex items-start justify-between gap-3 rounded-lg border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-2">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-semibold text-[#1E40AF]">
            {formatarNumeroCnj(selecionado.nu_processo)}
          </p>
          {polos ? <p className="truncate text-[12px] text-[#3B82F6]">{polos}</p> : null}
        </div>
        <button
          type="button"
          aria-label="Remover vínculo com o processo"
          onClick={() => onChange(null)}
          className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[#3B82F6] transition-colors hover:bg-[#DBEAFE] hover:text-[#1E40AF]"
        >
          <X className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>
    )
  }

  const itens = (resultados.data ?? []).slice(0, RESULTADOS_VISIVEIS)

  return (
    <div className="min-w-0">
      <div className="relative">
        <Search
          className="pointer-events-none absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]"
          aria-hidden
        />
        <input
          value={texto}
          aria-label="Buscar processo para vincular"
          placeholder="Buscar por número, classe ou parte"
          onChange={(event) => setTexto(event.target.value)}
          className="h-9 w-full rounded-lg border border-[#E5E7EB] bg-white pr-3 pl-9 text-[13px] text-[#111827] transition-colors outline-none placeholder:text-[#9CA3AF] hover:border-[#BFDBFE] focus:border-[#2563EB] focus:ring-2 focus:ring-[#DBEAFE]"
        />
      </div>
      <div className="mt-2 max-h-44 overflow-y-auto rounded-lg border border-[#E5E7EB]">
        {resultados.isLoading ? (
          <p className="px-3 py-2 text-[12px] text-[#6B7280]">Buscando processos…</p>
        ) : resultados.isError ? (
          <p className="px-3 py-2 text-[12px] text-[#B91C1C]">
            Não foi possível buscar os processos.
          </p>
        ) : itens.length === 0 ? (
          <p className="px-3 py-2 text-[12px] text-[#6B7280]">Nenhum processo encontrado.</p>
        ) : (
          <ul>
            {itens.map((processo) => {
              const autor = nomeDaParte(processo.parte_ativa)
              const reu = nomeDaParte(processo.parte_passiva)
              const polos = [autor, reu].filter(Boolean).join(' × ')
              return (
                <li key={processo.id}>
                  <button
                    type="button"
                    onClick={() =>
                      onChange({
                        id: processo.id,
                        nu_processo: processo.nu_processo,
                        autor,
                        reu,
                      })
                    }
                    className="block w-full px-3 py-2 text-left transition-colors hover:bg-[#EFF6FF]"
                  >
                    <span className="block truncate text-[13px] font-medium text-[#111827]">
                      {formatarNumeroCnj(processo.nu_processo)}
                    </span>
                    {polos ? (
                      <span className="block truncate text-[12px] text-[#6B7280]">{polos}</span>
                    ) : null}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
