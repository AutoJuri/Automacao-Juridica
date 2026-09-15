import { createFileRoute } from '@tanstack/react-router'

import { PushRobosPage } from '#/features/push/PushRobosPage'
import { requireAuth } from '#/lib/route-guards'

export const Route = createFileRoute('/push-robos')({
  beforeLoad: requireAuth,
  component: PushRobosPage,
})
