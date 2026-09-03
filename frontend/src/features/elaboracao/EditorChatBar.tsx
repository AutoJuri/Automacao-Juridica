import { Highlighter, Scale, MessageSquare, Sparkles } from 'lucide-react'
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
}

export function EditorChatBar({
  chatInput,
  onChange,
  highlightAtivo,
  iconesJuris,
  onToggleHighlight,
  onToggleIcones,
}: EditorChatBarProps) {
  return (
    <div className="border-t border-[#E5E7EB] bg-white px-4 py-3.5 shrink-0">
      <div className="flex items-center gap-3 max-w-[960px] mx-auto">
        <div className="relative flex-1 min-w-0">
          <MessageSquare className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#2563EB] pointer-events-none" />
          <input
            value={chatInput}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Chat para interação com a IA (ex: 'Inclua preliminar de prescrição')..."
            className={`w-full h-12 rounded-xl border border-[#E5E7EB] bg-[#F8F9FC] pl-10 pr-3 text-[13px] text-[#111827] placeholder:text-[#9CA3AF] ${FOCO_CAMPO}`}
            {...propsFocoCampo}
          />
        </div>
        <button
          type="button"
          disabled
          title="Geração de peça ainda não está em operação"
          className="h-12 px-5 rounded-xl bg-[#2563EB] text-white text-[13px] font-semibold tracking-wide opacity-50 shrink-0 inline-flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4" aria-hidden />
          Elaborar
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
        <p className="text-[11px] text-[#9CA3AF]">
          Dica: pressione Enter para elaborar com IA — ainda não está ligada.
        </p>
      </div>
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
