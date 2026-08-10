import { Outlet, createRootRoute } from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'
import { QueryClientProvider } from '@tanstack/react-query'

import { queryClient } from '#/lib/query-client'
import { ensureSessionRestored } from '#/lib/session-bootstrap'

import '../styles.css'

export const Route = createRootRoute({
  // Resolve a sessão antes de qualquer rota filha decidir se redireciona:
  // sem isso, um F5 em rota protegida cairia no login mesmo com cookie válido.
  beforeLoad: () => ensureSessionRestored(),
  component: RootComponent,
})

function RootComponent() {
  return (
    <QueryClientProvider client={queryClient}>
      <Outlet />
      <TanStackDevtools
        config={{
          position: 'bottom-right',
        }}
        plugins={[
          {
            name: 'TanStack Router',
            render: <TanStackRouterDevtoolsPanel />,
          },
        ]}
      />
    </QueryClientProvider>
  )
}
