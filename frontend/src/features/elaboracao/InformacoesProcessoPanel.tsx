import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import { CAMPO_VAZIO, extrairDadosElaboracao } from './elaboracao.processo'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

interface InformacoesProcessoPanelProps {
  processo: ProcessoDetalhe | null
  carregando: boolean
}

export function InformacoesProcessoPanel({
  processo,
  carregando,
}: InformacoesProcessoPanelProps) {
  if (carregando || !processo) {
    return (
      <div className="flex flex-col min-h-[160px]">
        <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase mb-3">
          Informações do processo
        </p>
        <EstadoCarregando mensagem="Carregando dados do e-SAJ…" />
      </div>
    )
  }

  const dados = extrairDadosElaboracao(processo)

  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-3">
        <p className="text-[11px] font-semibold text-[#9CA3AF] tracking-[0.18em] uppercase">
          Informações do processo
        </p>
        <span className="text-[10px] font-semibold text-[#15803D] bg-[#F0FDF4] border border-[#BBF7D0] rounded-md px-2 py-0.5">
          Ativo
        </span>
      </div>

      <Campo rotulo="Nº do processo" valor={dados.cnj} />

      <div className="grid grid-cols-2 gap-2 mt-2.5">
        <Campo rotulo="Autor" valor={dados.autor} />
        <Campo rotulo="Réu" valor={dados.reu} />
      </div>

      <div className="mt-2.5">
        <Campo rotulo="Foro / tribunal" valor={dados.foroTribunal} />
      </div>

      <div className="mt-2.5">
        <Campo rotulo="Valor da causa" valor={dados.valorCausa} />
      </div>
    </div>
  )
}

function Campo({ rotulo, valor }: { rotulo: string; valor: string }) {
  const vazio = valor === CAMPO_VAZIO || valor === 'Ainda não buscado no CPO'
  return (
    <label className="block min-w-0">
      <span className="text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-widest">
        {rotulo}
      </span>
      <input
        readOnly
        value={valor}
        title="Dado coletado do e-SAJ — não é editável daqui"
        className={[
          'mt-1 w-full h-9 rounded-lg border border-[#E5E7EB] bg-[#F8F9FC] px-2.5 text-[13px]',
          vazio ? 'text-[#9CA3AF] italic' : 'text-[#111827]',
          FOCO_CAMPO,
        ].join(' ')}
        {...propsFocoCampo}
      />
    </label>
  )
}
