import { AlertCircle, CheckCircle2 } from 'lucide-react'

/** Erro de validação de um campo específico. */
export function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null
  }

  return <p className="text-xs text-[#DC2626] mt-1.5">{message}</p>
}

/** Banner de erro da API, acima do formulário. */
export function FormError({ message }: { message: string | null }) {
  if (!message) {
    return null
  }

  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-md border border-[#FECACA] bg-[#FEF2F2] px-3 py-2.5"
    >
      <AlertCircle className="w-4 h-4 shrink-0 mt-px text-[#DC2626]" />
      <p className="text-xs leading-relaxed text-[#991B1B]">{message}</p>
    </div>
  )
}

/** Banner de confirmação, usado nos fluxos de recuperação de senha. */
export function FormSuccess({ message }: { message: string }) {
  return (
    <div
      role="status"
      className="flex items-start gap-2 rounded-md border border-[#BBF7D0] bg-[#F0FDF4] px-3 py-2.5"
    >
      <CheckCircle2 className="w-4 h-4 shrink-0 mt-px text-[#16A34A]" />
      <p className="text-xs leading-relaxed text-[#166534]">{message}</p>
    </div>
  )
}
