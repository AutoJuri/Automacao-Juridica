import { createLazyFileRoute } from '@tanstack/react-router'

import { ConvitePage } from '#/features/organizations/ConvitePage'

export const Route = createLazyFileRoute('/convite/$token')({
  component: function ConviteRoute() {
    const { token } = Route.useParams()
    return <ConvitePage token={token} />
  },
})
