import { useQuery } from '@tanstack/react-query'

import { buscarDossie, dossieQueryKey } from './dossie.api'
import { deveAcompanhar, percentualLeitura, rotuloFaixaAutos } from './dossie.estado'

export function useDossie(processoId: string) {
  return useQuery({
    queryKey: dossieQueryKey(processoId),
    queryFn: () => buscarDossie(processoId),
    staleTime: 15_000,
    refetchInterval: (query) => (deveAcompanhar(query.state.data?.status) ? 3000 : false),
  })
}

export function FaixaAutos({ processoId }: { processoId: string }) {
  const consulta = useDossie(processoId)
  const dados = consulta.data
  const lidos = dados?.lidos ?? 0
  const total = dados?.total ?? 0
  const percentual = percentualLeitura(lidos, total)
  const rotulo = consulta.isLoading
    ? 'Autos'
    : rotuloFaixaAutos(dados?.status, lidos, total)

  return (
    <div>
      <div className="flex items-center justify-between gap-2 text-[11px] text-[#6B7280]">
        <span>{rotulo}</span>
        {total > 0 ? <span>{percentual}%</span> : null}
      </div>
      <div
        className="mt-1 h-1.5 overflow-hidden rounded-full bg-[#E5E7EB]"
        role="progressbar"
        aria-valuenow={percentual}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={rotulo}
      >
        <div className="h-full rounded-full bg-[#2563EB]" style={{ width: `${percentual}%` }} />
      </div>
    </div>
  )
}
