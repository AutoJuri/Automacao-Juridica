import { AppChrome } from '#/features/processos/AppChrome'

interface SecaoPlaceholderPageProps {
  titulo: string
  descricao: string
}

/** Página em branco das seções que ainda não têm módulo próprio. */
export function SecaoPlaceholderPage({ titulo, descricao }: SecaoPlaceholderPageProps) {
  return (
    <AppChrome contentClassName="flex-1 overflow-y-auto px-5 sm:px-8 lg:px-10 xl:px-14 py-8">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold text-[#111827]">{titulo}</h1>
        <p className="mt-2 text-sm text-[#6B7280] leading-relaxed">{descricao}</p>
      </div>
    </AppChrome>
  )
}
