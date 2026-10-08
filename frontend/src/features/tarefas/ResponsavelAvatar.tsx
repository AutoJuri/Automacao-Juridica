import { iniciais } from './tarefas.texto'

export function ResponsavelAvatar({ nome }: { nome: string }) {
  return (
    <span
      title={nome}
      aria-label={nome}
      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#EFF6FF] text-[11px] font-semibold text-[#2563EB]"
    >
      {iniciais(nome)}
    </span>
  )
}
