import { createLazyFileRoute } from '@tanstack/react-router'

import { OrganizacaoMembrosPage } from '#/features/organizations/OrganizacaoMembrosPage'

export const Route = createLazyFileRoute('/organizacoes/$orgId')({
  component: function OrganizacaoRoute() {
    const { orgId } = Route.useParams()
    return <OrganizacaoMembrosPage orgId={orgId} />
  },
})
