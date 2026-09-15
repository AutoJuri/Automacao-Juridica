import { createFileRoute, redirect } from '@tanstack/react-router'

import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/gerencias')({
  beforeLoad: () => {
    requireAuth()
    throw redirect({ to: '/', replace: true })
  },
  component: () => null,
})
