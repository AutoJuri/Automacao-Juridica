import { createLazyFileRoute } from '@tanstack/react-router'

import { DrivePage } from '#/features/drive/DrivePage'

export const Route = createLazyFileRoute('/drive/')({
  component: DrivePage,
})
