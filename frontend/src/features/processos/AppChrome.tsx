import type { CSSProperties, ReactNode } from 'react'
import { useRouterState } from '@tanstack/react-router'

import { AppSidebar } from './AppSidebar'
import { Navbar, NAVBAR_HEIGHT } from './Navbar'
import { SIDEBAR_WIDTH, estaEmGerencias } from './nav.constants'

interface AppChromeProps {
  children: ReactNode
  onAbrirProcesso?: (processoId: string) => void
  contentClassName?: string
  contentStyle?: CSSProperties
}

/** Navbar em todas as rotas autenticadas; rail só dentro de Gerências. */
export function AppChrome({
  children,
  onAbrirProcesso,
  contentClassName,
  contentStyle,
}: AppChromeProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const comSidebar = estaEmGerencias(pathname)

  return (
    <div
      className="flex flex-col h-screen bg-[#F0F2F7] overflow-hidden"
      style={{ '--navbar-height': `${NAVBAR_HEIGHT}px` } as CSSProperties}
    >
      <Navbar onAbrirProcesso={onAbrirProcesso} />
      {comSidebar ? <AppSidebar /> : null}
      <div
        className={contentClassName}
        style={{
          marginTop: NAVBAR_HEIGHT,
          marginLeft: comSidebar ? SIDEBAR_WIDTH : 0,
          ...contentStyle,
        }}
      >
        {children}
      </div>
    </div>
  )
}
