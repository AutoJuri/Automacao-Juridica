import { Link, useMatchRoute } from '@tanstack/react-router'
import { Calendar, Layers, Radio, Search } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { cn } from '#/lib/utils'
import { NAVBAR_HEIGHT } from './Navbar'
import {
  SECOES_LATERAL,
  SIDEBAR_WIDTH,
  type IconeLateral,
} from './nav.constants'

const ICONES: Record<IconeLateral, LucideIcon> = {
  layers: Layers,
  search: Search,
  calendar: Calendar,
  radio: Radio,
}

export function AppSidebar() {
  const matchRoute = useMatchRoute()

  return (
    <aside
      aria-label="Seções de Gerências"
      className="fixed left-0 bottom-0 z-40 flex flex-col items-center border-r border-[#E5E7EB] bg-white pt-4 pb-5"
      style={{ top: NAVBAR_HEIGHT, width: SIDEBAR_WIDTH }}
    >
      <nav className="flex flex-1 flex-col items-center gap-2">
        {SECOES_LATERAL.map((item) => {
          const ativo = Boolean(matchRoute({ to: item.to, fuzzy: false }))
          const Icone = ICONES[item.icone]

          return (
            <Link
              key={item.to}
              to={item.to}
              aria-label={item.label}
              aria-current={ativo ? 'page' : undefined}
              className="group relative flex h-14 w-14 items-center justify-center"
            >
              <span
                className={cn(
                  'relative flex h-12 w-12 items-center justify-center rounded-xl transition-colors',
                  ativo
                    ? 'bg-[#2563EB] text-white shadow-sm'
                    : 'text-[#6B7280] group-hover:bg-[#F3F4F6] group-hover:text-[#111827]',
                )}
              >
                <Icone className="h-6 w-6" strokeWidth={1.75} />
              </span>
              <span
                className={cn(
                  'pointer-events-none absolute left-[calc(100%+10px)] z-[70] whitespace-nowrap rounded-md bg-[#111827] px-2 py-1',
                  'text-[11px] font-medium text-white shadow-lg',
                  'opacity-0 translate-x-1 transition-all duration-150',
                  'group-hover:opacity-100 group-hover:translate-x-0',
                )}
              >
                {item.label}
              </span>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
