import { useNavigate } from '@tanstack/react-router'
import { LogOut, Scale } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { useAuthStore } from '#/store/auth.store'

export const NAVBAR_HEIGHT = 64

export function Navbar() {
  const navigate = useNavigate()
  const clearAuth = useAuthStore((s) => s.clearAuth)

  function handleLogout() {
    // Mock: limpa auth em memória e redireciona — sem chamada real de API por enquanto
    clearAuth()
    navigate({ to: '/login', replace: true })
  }

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 lg:px-12 bg-[#0D0F14] border-b border-white/[0.06]"
      style={{ height: NAVBAR_HEIGHT }}
    >
      {/* Left — brand */}
      <div className="flex items-center gap-3.5">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#8B5CF6]">
          <Scale className="w-4 h-4 text-white" />
        </div>
        <div className="flex flex-col leading-none gap-1">
          <span className="text-white text-[15px] font-semibold tracking-tight">
            AdvogAtiva Secure Hub
          </span>
          <span className="text-[#3B5BDB] text-[10px] font-medium tracking-[0.18em] uppercase">
            Acompanhamento de Autos Ativos
          </span>
        </div>
      </div>

      {/* Right — status + logout */}
      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#22C55E] opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#22C55E]" />
          </span>
          <span className="text-[#22C55E] text-[11px] font-semibold tracking-[0.16em] uppercase">
            Auditoria Digital
          </span>
          <span className="text-white/25 text-[11px]">·</span>
          <span className="text-white/50 text-[11px] tracking-[0.12em] uppercase">
            GCM
          </span>
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          className="h-8 gap-1.5 px-3 text-[11px] font-medium text-white/70 hover:text-white hover:bg-white/10 border border-white/10"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sair
        </Button>
      </div>
    </header>
  )
}
