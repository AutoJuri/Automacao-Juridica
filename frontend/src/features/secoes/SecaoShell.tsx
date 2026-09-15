import type { ReactNode } from 'react'
import { AppChrome } from '#/features/processos/AppChrome'

interface SecaoShellProps {
  children: ReactNode
  /** Se falso, a área abaixo da navbar não rola — a página controla o overflow. */
  scroll?: boolean
}

export function SecaoShell({ children, scroll = true }: SecaoShellProps) {
  return (
    <AppChrome
      contentClassName={[
        'flex-1 min-h-0 flex flex-col px-8 sm:px-12 lg:px-20 xl:px-28 2xl:px-36 py-6',
        scroll ? 'overflow-y-auto' : 'overflow-hidden',
      ].join(' ')}
    >
      {children}
    </AppChrome>
  )
}
