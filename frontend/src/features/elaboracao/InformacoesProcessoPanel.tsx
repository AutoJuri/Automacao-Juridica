import type { ProcessoDetalhe } from '#/features/processos/processos.types'
import { EstadoCarregando } from '#/features/secoes/EstadoCarregando'
import type { CamposManuais } from './elaboracao.manual'
import { CAMPO_VAZIO, extrairDadosElaboracao } from './elaboracao.processo'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

interface InformacoesProcessoPanelProps {
  processo: ProcessoDetalhe | null
  carregando: boolean
  semProcesso?: boolean
  campos?: CamposManuais
  onCampos?: (campos: CamposManuais) => void
  onCamposBlur?: () => void
}

export function InformacoesProcessoPanel({
  processo,
  carregando,
  semProcesso = false,
  campos,
  onCampos,
  onCamposBlur,
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
        {semProcesso ? (
          <span className="text-[10px] font-semibold text-[#6B7280] bg-[#F3F4F6] border border-[#E5E7EB] rounded-md px-2 py-0.5">
            Sem processo vinculado
          </span>
        ) : (
          <span className="text-[10px] font-semibold text-[#15803D] bg-[#F0FDF4] border border-[#BBF7D0] rounded-md px-2 py-0.5">
            Ativo
          </span>
        )}
      </div>

      {semProcesso && campos && onCampos ? (
        <CamposEditaveis campos={campos} onCampos={onCampos} onBlur={onCamposBlur} />
      ) : (
        <>
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
        </>
      )}
    </div>
  )
}

function CamposEditaveis({
  campos,
  onCampos,
  onBlur,
}: {
  campos: CamposManuais
  onCampos: (campos: CamposManuais) => void
  onBlur?: () => void
}) {
  function alterar(campo: keyof CamposManuais, valor: string) {
    onCampos({ ...campos, [campo]: valor })
  }

  return (
    <div
      onBlur={(event) => {
        const destino = event.relatedTarget
        if (destino instanceof Node && event.currentTarget.contains(destino)) {
          return
        }
        onBlur?.()
      }}
    >
      <CampoLivre
        rotulo="Nº do processo"
        valor={campos.nu_processo}
        placeholder="Número do processo"
        maxLength={50}
        onChange={(valor) => alterar('nu_processo', valor)}
      />
      <div className="grid grid-cols-2 gap-2 mt-2.5">
        <CampoLivre
          rotulo="Autor"
          valor={campos.parte_ativa}
          placeholder="Nome do autor"
          maxLength={255}
          onChange={(valor) => alterar('parte_ativa', valor)}
        />
        <CampoLivre
          rotulo="Réu"
          valor={campos.parte_passiva}
          placeholder="Nome do réu"
          maxLength={255}
          onChange={(valor) => alterar('parte_passiva', valor)}
        />
      </div>
      <div className="mt-2.5">
        <CampoLivre
          rotulo="Foro / tribunal"
          valor={campos.foro_vara}
          placeholder="Foro ou vara"
          maxLength={255}
          onChange={(valor) => alterar('foro_vara', valor)}
        />
      </div>
      <div className="mt-2.5">
        <CampoLivre
          rotulo="Valor da causa"
          valor={campos.valor_causa}
          placeholder="Valor da causa"
          maxLength={100}
          onChange={(valor) => alterar('valor_causa', valor)}
        />
      </div>
    </div>
  )
}

function CampoLivre({
  rotulo,
  valor,
  placeholder,
  maxLength,
  onChange,
}: {
  rotulo: string
  valor: string
  placeholder: string
  maxLength: number
  onChange: (valor: string) => void
}) {
  return (
    <label className="block min-w-0">
      <span className="text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-widest">
        {rotulo}
      </span>
      <input
        value={valor}
        placeholder={placeholder}
        maxLength={maxLength}
        onChange={(event) => onChange(event.target.value)}
        className={`mt-1 w-full h-9 rounded-lg border border-[#E5E7EB] bg-white px-2.5 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] placeholder:not-italic ${FOCO_CAMPO}`}
        {...propsFocoCampo}
      />
    </label>
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
