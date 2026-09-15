import { Loader2 } from 'lucide-react'

interface EstadoCarregandoProps {
  mensagem: string
  /** Preenche o container pai (precisa de flex no pai). */
  preencher?: boolean
  /** Spinner + texto em linha, para formulários e cards estreitos. */
  compacto?: boolean
}

/** Loading centralizado com círculo — use dentro de cards/listas que ocupam a tela. */
export function EstadoCarregando({
  mensagem,
  preencher = true,
  compacto = false,
}: EstadoCarregandoProps) {
  return (
    <div
      className={[
        'flex items-center justify-center px-4',
        compacto ? 'py-3' : preencher ? 'flex-1 min-h-[180px] w-full h-full' : 'py-10',
      ].join(' ')}
      role="status"
      aria-live="polite"
    >
      <div className={compacto ? 'flex items-center gap-2.5' : 'flex flex-col items-center gap-3'}>
        <Loader2
          className={[
            'animate-spin text-[#2563EB] shrink-0',
            compacto ? 'w-5 h-5' : 'w-8 h-8',
          ].join(' ')}
          aria-hidden
        />
        <p className="text-sm text-[#6B7280]">{mensagem}</p>
      </div>
    </div>
  )
}
