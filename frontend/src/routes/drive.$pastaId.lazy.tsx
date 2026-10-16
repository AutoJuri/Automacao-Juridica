import { createLazyFileRoute } from '@tanstack/react-router'

import { PastaPage } from '#/features/drive/PastaPage'

export const Route = createLazyFileRoute('/drive/$pastaId')({
  component: function PastaRoute() {
    const { pastaId } = Route.useParams()
    return <PastaPage pastaId={pastaId} />
  },
})
