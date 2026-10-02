import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'
import { ElaboracaoPage } from '#/features/elaboracao/ElaboracaoPage'
import { requireAuth } from '#/lib/route-guards'

// `peca` viaja do card "Ação sugerida" do cabeçalho do processo quando há
// sugestão (ADR-016 Fase 1) — pré-seleciona o seletor, que continua livre.
const searchSchema = z.object({
  peca: z.string().optional().catch(undefined),
})

export const Route = createFileRoute('/elaboracao/$processoId')({
  beforeLoad: requireAuth,
  validateSearch: searchSchema,
  component: function ElaboracaoRoute() {
    const { processoId } = Route.useParams()
    const { peca } = Route.useSearch()
    return <ElaboracaoPage processoId={processoId} pecaSugeridaNaUrl={peca ?? null} />
  },
})
