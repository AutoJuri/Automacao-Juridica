import { Highlighter, Loader2, Scale, MessageSquare, Send, Sparkles } from 'lucide-react'
import { Switch } from '#/components/ui/switch'
import { Label } from '#/components/ui/label'
import { FOCO_CAMPO, propsFocoCampo } from './elaboracao.ui'

interface EditorChatBarProps {
  chatInput: string
  onChange: (v: string) => void
  highlightAtivo: boolean
  iconesJuris: boolean
  onToggleHighlight: (v: boolean) => void
  onToggleIcones: (v: boolean) => void
  podeElaborar: boolean
  elaborando: boolean
  onElaborar: () => void
  podeConversar: boolean
  enviandoChat: boolean
  onEnviarChat: () => void
  erro: string | null
}

export function EditorChatBar({
  chatInput,
  onChange,
  highlightAtivo,
  iconesJuris,
  onToggleHighlight,
  onToggleIcones,
  podeElaborar,
  elaborando,
  onElaborar,
  podeConversar,
  enviandoChat,
  onEnviarChat,
  erro,
}: EditorChatBarProps) {
  const instrucao = chatInput.trim()
  const modoEnviar = podeConversar && instrucao.length > 0
  const ocupado = elaborando || enviandoChat
  const dica = modoEnviar
    ? 'Enter ou Enviar aplica a instrução na minuta atual.'
    : podeConversar
      ? 'Com o campo vazio, Elaborar gera o rascunho de novo.'
      : 'Clique em Elaborar para gerar o primeiro rascunho. O campo abre depois disso.'

  function acionar() {
    if (modoEnviar) {
      onEnviarChat()
      return
    }
    onElaborar()
  }

  return (
    <div className="border-t border-[#E5E7EB] bg-white px-4 py-3.5 shrink-0">
      <div className="flex items-center gap-3 max-w-[960px] mx-auto">
        <div className="relative flex-1 min-w-0">
          <MessageSquare className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#2563EB] pointer-events-none" />
          <input
            value={chatInput}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== 'Enter' || e.shiftKey) {
                return
              }
              e.preventDefault()
              if (modoEnviar && !ocupado) {
                onEnviarChat()
              }
            }}
            disabled={!podeConversar || enviandoChat}
            placeholder={
              podeConversar
                ? "Descreva a alteração na minuta e envie (ex.: 'Inclua preliminar de prescrição')"
                : 'Elabore o primeiro rascunho para descrever alterações aqui'
            }
            className={`w-full h-12 rounded-xl border border-[#E5E7EB] bg-[#F8F9FC] pl-10 pr-3 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] disabled:opacity-60 disabled:cursor-not-allowed ${FOCO_CAMPO}`}
            {...propsFocoCampo}
          />
        </div>
        <button
          type="button"
          disabled={modoEnviar ? ocupado : !podeElaborar || ocupado}
          onClick={acionar}
          title={
            modoEnviar
              ? 'Enviar instrução para editar a minuta'
              : podeElaborar
                ? 'Gerar rascunho com a IA'
                : 'Carregando sessão de elaboração…'
          }
          className="h-12 px-5 rounded-xl bg-[#2563EB] text-white text-[13px] font-semibold tracking-wide shrink-0 inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#1D4ED8]"
        >
          {ocupado ? (
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
          ) : modoEnviar ? (
            <Send className="w-4 h-4" aria-hidden />
          ) : (
            <Sparkles className="w-4 h-4" aria-hidden />
          )}
          {modoEnviar ? 'Enviar' : 'Elaborar'}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 max-w-[960px] mx-auto mt-3">
        <ToggleLinha
          id="toggle-highlight"
          label="Modo Highlight / Grifo de Seleção"
          icon={Highlighter}
          checked={highlightAtivo}
          onChange={onToggleHighlight}
        />
        <ToggleLinha
          id="toggle-icones"
          label="Ícones de Jurisprudência no Texto"
          icon={Scale}
          checked={iconesJuris}
          onChange={onToggleIcones}
        />
        <p className="text-[11px] text-[#9CA3AF]">{dica}</p>
      </div>

      {erro ? (
        <p className="max-w-[960px] mx-auto mt-2 text-[12px] text-[#B91C1C] bg-[#FEF2F2] border border-[#FECACA] rounded-md px-2.5 py-1.5">
          {erro}
        </p>
      ) : null}
    </div>
  )
}

function ToggleLinha({
  id,
  label,
  icon: Icon,
  checked,
  onChange,
}: {
  id: string
  label: string
  icon: typeof Highlighter
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center gap-2">
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
      <Label htmlFor={id} className="flex items-center gap-2 text-[12px] text-[#4B5563] cursor-pointer">
        <Icon className="w-4 h-4 text-[#2563EB] shrink-0" aria-hidden />
        {label}
      </Label>
    </div>
  )
}
