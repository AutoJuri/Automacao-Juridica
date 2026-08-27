import { Navbar, NAVBAR_HEIGHT } from '#/features/processos/Navbar'

interface SecaoPlaceholderPageProps {
  titulo: string
  descricao: string
}

/** Página em branco das seções da navbar que ainda não têm módulo próprio. */
export function SecaoPlaceholderPage({ titulo, descricao }: SecaoPlaceholderPageProps) {
  return (
    <div className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden">
      <Navbar />

      <div
        className="flex-1 overflow-y-auto px-5 sm:px-8 lg:px-10 xl:px-14 py-8"
        style={{ marginTop: NAVBAR_HEIGHT }}
      >
        <div className="max-w-2xl">
          <h1 className="text-2xl font-semibold text-[#111827]">{titulo}</h1>
          <p className="mt-2 text-sm text-[#6B7280] leading-relaxed">{descricao}</p>
        </div>
      </div>
    </div>
  )
}
