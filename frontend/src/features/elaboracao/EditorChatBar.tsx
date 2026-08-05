import { Send, Sparkles } from 'lucide-react'
import { Textarea } from '#/components/ui/textarea'
import { Button } from '#/components/ui/button'

interface EditorChatBarProps {
  chatInput: string
  onChange: (v: string) => void
}

export function EditorChatBar({ chatInput, onChange }: EditorChatBarProps) {
  return (
    <div className="border-t border-[#E5E7EB] bg-white px-4 py-3 shrink-0">
      <div className="flex items-end gap-3 max-w-[780px] mx-auto">
        <div className="flex-1 relative">
          <Sparkles className="absolute left-3 top-2.5 w-3.5 h-3.5 text-[#9CA3AF] pointer-events-none" />
          <Textarea
            value={chatInput}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Instrua a IA para alterar a peça... (ex: adicione preliminar de ilegitimidade passiva)"
            className="resize-none pl-8 pr-4 py-2 text-[13px] min-h-[40px] max-h-[100px] border-[#E5E7EB] focus:border-[#3B5BDB] focus:ring-1 focus:ring-[#3B5BDB] rounded-lg"
            rows={1}
          />
        </div>

        <Button
          size="sm"
          className="h-9 px-4 text-[11px] font-semibold gap-1.5 text-[#6B7280] bg-transparent border border-[#E5E7EB] hover:bg-[#F3F4F6] hover:text-[#111827] shrink-0"
          variant="outline"
        >
          <Send className="w-3.5 h-3.5" />
          Enviar
        </Button>

        <Button
          size="default"
          className="h-9 px-6 text-[13px] font-bold gap-2 bg-[#3B5BDB] hover:bg-[#2d4cba] text-white shrink-0 tracking-wide"
        >
          <Sparkles className="w-4 h-4" />
          ELABORAR
        </Button>
      </div>
    </div>
  )
}
