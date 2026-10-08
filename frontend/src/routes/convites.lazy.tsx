import { createLazyFileRoute } from '@tanstack/react-router'

import { ConvitesRecebidosPage } from '#/features/organizations/ConvitesRecebidosPage'

export const Route = createLazyFileRoute('/convites')({
  component: ConvitesRecebidosPage,
})
