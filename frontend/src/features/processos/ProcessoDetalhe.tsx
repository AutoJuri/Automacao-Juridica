import { useQuery } from '@tanstack/react-query'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { ProcessoAndamentos } from './ProcessoAndamentos'
import { ProcessoCabecalho } from './ProcessoCabecalho'
import { buscarProcesso } from './processos.api'
import { processoDetalheQueryKey } from './processos.constants'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'

interface ProcessoDetalheProps {
  processoId: string | null
}

function EstadoVazio({ mensagem }: { mensagem: string }) {
  return (
    <div className="flex-1 flex items-center justify-center rounded-2xl border border-[#E5E7EB] bg-white min-h-[200px] shadow-sm">
      <p className="text-[#9CA3AF] text-sm px-6 text-center">{mensagem}</p>
    </div>
  )
}

export function ProcessoDetalhe({ processoId }: ProcessoDetalheProps) {
  const detalheQuery = useQuery({
    queryKey: processoId ? processoDetalheQueryKey(processoId) : ['processos', 'nenhum'],
    queryFn: () => buscarProcesso(processoId as string),
    enabled: Boolean(processoId),
  })

  if (!processoId) {
    return (
      <EstadoVazio mensagem="Nenhum processo selecionado ou nenhum resultado para os filtros aplicados." />
    )
  }

  if (detalheQuery.isLoading) {
    return (
      <div className="flex-1 flex flex-col rounded-2xl border border-[#E5E7EB] bg-white min-h-[200px] shadow-sm">
        <EstadoCarregando mensagem="Carregando processo…" />
      </div>
    )
  }

  if (detalheQuery.isError || !detalheQuery.data) {
    return (
      <EstadoVazio
        mensagem={mensagemDeErro(detalheQuery.error, { 404: 'Processo não encontrado.' })}
      />
    )
  }

  const processo = detalheQuery.data

  return (
    <div className="flex flex-col gap-4 min-w-0 pb-2">
      <ProcessoCabecalho processo={processo} />
      <ProcessoAndamentos
        processoId={processo.id}
        movimentacoes={processo.movimentacoes}
        status={processo.movimentacoes_status}
        urlCpo={processo.url_cpo}
        numeroProcesso={processo.nu_processo}
      />
    </div>
  )
}
