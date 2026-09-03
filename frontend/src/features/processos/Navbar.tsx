import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useRouterState } from '@tanstack/react-router'
import {
  Bell,
  Briefcase,
  FolderOpen,
  ListTodo,
  LogOut,
  PenLine,
  Scale,
  Settings,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '#/components/ui/button'
import { logout } from '#/features/auth/auth.api'
import {
  listarNotificacoes,
  marcarNotificacaoLida,
  marcarTodasNotificacoesLidas,
} from '#/features/notificacoes/notifications.api'
import { NOTIFICATIONS_QUERY_KEY } from '#/features/notificacoes/notifications.constants'
import { cn } from '#/lib/utils'
import { limparQueriesDaSessao } from '#/lib/session-queries'
import { useAuthStore } from '#/store/auth.store'
import { SECOES_TOPO, secaoTopoAtiva, type IconeTopo } from './nav.constants'
import { formatarDataHoraSP } from './processos.dates'

const ICONES_TOPO: Record<IconeTopo, LucideIcon> = {
  briefcase: Briefcase,
  pen: PenLine,
  folder: FolderOpen,
  check: ListTodo,
}

export const NAVBAR_HEIGHT = 72

interface NavbarProps {
  onAbrirProcesso?: (processoId: string) => void
}

export function Navbar({ onAbrirProcesso }: NavbarProps) {
  const navigate = useNavigate()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const queryClient = useQueryClient()
  const [aberto, setAberto] = useState(false)
  const painelRef = useRef<HTMLDivElement>(null)

  const notificacoesQuery = useQuery({
    queryKey: NOTIFICATIONS_QUERY_KEY,
    queryFn: () => listarNotificacoes(false),
  })

  const notificacoes = notificacoesQuery.data ?? []
  const naoLidas = notificacoes.filter((n) => !n.is_read).length

  const marcarUma = useMutation({
    mutationFn: marcarNotificacaoLida,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
    },
  })

  const marcarTodas = useMutation({
    mutationFn: marcarTodasNotificacoesLidas,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
    },
  })

  useEffect(() => {
    if (!aberto) {
      return
    }
    function fechar(evento: MouseEvent) {
      if (painelRef.current && !painelRef.current.contains(evento.target as Node)) {
        setAberto(false)
      }
    }
    document.addEventListener('mousedown', fechar)
    return () => document.removeEventListener('mousedown', fechar)
  }, [aberto])

  const sair = useMutation({
    mutationFn: logout,
    onSettled: () => {
      clearAuth()
      limparQueriesDaSessao(queryClient)
      navigate({ to: '/login', replace: true })
    },
  })

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 flex items-center gap-4 px-4 lg:px-6 xl:px-8 bg-navbar border-b border-border-subtle"
      style={{ height: NAVBAR_HEIGHT }}
    >
      <Link to="/" className="flex items-center gap-3 shrink-0 min-w-0">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#2563EB] shrink-0">
          <Scale className="w-4 h-4 text-white" />
        </div>
        <div className="flex flex-col leading-none gap-1 min-w-0">
          <span className="text-[#111827] text-[15px] font-semibold tracking-tight truncate">
            AdvogAtiva Secure Hub
          </span>
          <span className="text-[#9CA3AF] text-[10px] font-medium tracking-[0.18em] uppercase hidden sm:block">
            Acompanhamento de Autos Ativos
          </span>
        </div>
      </Link>

      <nav
        aria-label="Áreas da plataforma"
        className="flex-1 min-w-0 self-stretch flex items-center px-2 lg:px-6"
      >
        <div className="flex w-full h-12 items-stretch rounded-2xl bg-[#EEF2F7] p-1">
          {SECOES_TOPO.map((item) => {
            const ativo = secaoTopoAtiva(item.to, pathname)
            const Icone = ICONES_TOPO[item.icone]
            return (
              <Link
                key={item.to}
                to={item.to}
                aria-current={ativo ? 'page' : undefined}
                className={cn(
                  'relative flex flex-1 min-w-0 items-center justify-center gap-2 rounded-xl text-[13px] lg:text-[14px] font-semibold tracking-tight transition-all',
                  ativo
                    ? 'bg-white text-[#2563EB] shadow-sm ring-1 ring-[#2563EB]/15'
                    : 'text-[#6B7280] hover:text-[#111827] hover:bg-white/60',
                )}
              >
                <Icone className="h-[18px] w-[18px] shrink-0" strokeWidth={2} />
                <span className="truncate">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      <div className="flex items-center gap-2 shrink-0">
        <div className="relative" ref={painelRef}>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setAberto((v) => !v)}
            aria-label="Notificações"
            className="relative h-9 w-9 px-0 text-[#4B5563] hover:text-[#111827] hover:bg-[#F3F4F6] border border-[#E5E7EB]"
          >
            <Bell className="w-4 h-4" />
            {naoLidas > 0 ? (
              <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-[#EF4444] text-[9px] font-bold text-white leading-4 text-center">
                {naoLidas > 9 ? '9+' : naoLidas}
              </span>
            ) : null}
          </Button>

          {aberto ? (
            <div className="absolute right-0 mt-2 w-[360px] max-w-[calc(100vw-2rem)] rounded-xl border border-[#E5E7EB] bg-white shadow-lg overflow-hidden z-50">
              <div className="flex items-center justify-between px-4 py-3 border-b border-[#E5E7EB]">
                <p className="text-[12px] font-semibold text-[#111827]">Notificações</p>
                <button
                  type="button"
                  disabled={naoLidas === 0 || marcarTodas.isPending}
                  onClick={() => marcarTodas.mutate()}
                  className="text-[11px] font-medium text-[#2563EB] disabled:text-[#9CA3AF]"
                >
                  Marcar todas como lidas
                </button>
              </div>
              <div className="max-h-[360px] overflow-y-auto">
                {notificacoes.length === 0 ? (
                  <p className="text-[12px] text-[#9CA3AF] px-4 py-8 text-center">
                    Nenhuma notificação no momento.
                  </p>
                ) : (
                  notificacoes.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        if (!item.is_read) {
                          marcarUma.mutate(item.id)
                        }
                        if (item.processo_id) {
                          if (onAbrirProcesso) {
                            onAbrirProcesso(item.processo_id)
                          } else {
                            void navigate({
                              to: '/',
                              search: { processo: item.processo_id },
                            })
                          }
                        }
                        setAberto(false)
                      }}
                      className={[
                        'w-full text-left px-4 py-3 border-b border-[#F3F4F6] hover:bg-[#F8F9FC]',
                        item.is_read ? 'opacity-70' : 'bg-[#FAF5FF]/40',
                      ].join(' ')}
                    >
                      <p className="text-[12px] font-semibold text-[#111827] leading-snug">
                        {item.titulo}
                      </p>
                      <p className="text-[11px] text-[#6B7280] leading-relaxed mt-0.5 line-clamp-2">
                        {item.message}
                      </p>
                      <p className="text-[10px] text-[#9CA3AF] tabular-nums mt-1">
                        {formatarDataHoraSP(item.created_at)}
                      </p>
                    </button>
                  ))
                )}
              </div>
            </div>
          ) : null}
        </div>

        <Button
          asChild
          variant="ghost"
          size="sm"
          className="h-9 gap-1.5 px-3 text-[13px] font-medium text-[#4B5563] hover:text-[#111827] hover:bg-[#F3F4F6] border border-[#E5E7EB]"
        >
          <Link to="/configuracoes">
            <Settings className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Configurações</span>
          </Link>
        </Button>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => sair.mutate()}
          disabled={sair.isPending}
          className="h-9 gap-1.5 px-3 text-[13px] font-medium text-[#4B5563] hover:text-[#111827] hover:bg-[#F3F4F6] border border-[#E5E7EB]"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sair
        </Button>
      </div>
    </header>
  )
}
