import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'

import { Button } from '#/components/ui/button'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import { useOrgStore } from '#/store/org.store'
import { aceitarConviteRecebido, listarConvitesRecebidos, recusarConviteRecebido } from './organizations.api'
import { ORGANIZATIONS_QUERY_KEY, RECEIVED_INVITES_QUERY_KEY } from './organizations.constants'
import { rotuloPapel } from './organizations.roles'

export function ConvitesRecebidosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setAtiva = useOrgStore((s) => s.setActiveOrganizationId)
  const lista = useQuery({
    queryKey: RECEIVED_INVITES_QUERY_KEY,
    queryFn: listarConvitesRecebidos,
  })

  function invalidar() {
    void queryClient.invalidateQueries({ queryKey: RECEIVED_INVITES_QUERY_KEY })
    void queryClient.invalidateQueries({ queryKey: ORGANIZATIONS_QUERY_KEY })
  }

  const aceitar = useMutation({
    mutationFn: aceitarConviteRecebido,
    onSuccess: (org) => {
      setAtiva(org.organization_id)
      invalidar()
      void navigate({ to: '/organizacoes/$orgId', params: { orgId: org.organization_id } })
    },
  })

  const recusar = useMutation({
    mutationFn: recusarConviteRecebido,
    onSuccess: invalidar,
  })

  const convites = lista.data ?? []

  return (
    <SecaoShell>
      <div className="max-w-2xl mx-auto w-full space-y-4">
        <header>
          <h1 className="text-2xl font-semibold text-[#111827]">Convites recebidos</h1>
          <p className="text-sm text-[#6B7280] mt-1">
            Convites pendentes para o e-mail da sua conta.
          </p>
        </header>

        {lista.isError ? (
          <p className="text-sm text-[#6B7280]">Não foi possível carregar os convites.</p>
        ) : convites.length === 0 ? (
          <p className="text-sm text-[#6B7280]">Nenhum convite pendente.</p>
        ) : (
          <ul className="space-y-3">
            {convites.map((convite) => (
              <li
                key={convite.id}
                className="rounded-xl border border-[#E5E7EB] bg-white p-4 flex flex-col sm:flex-row sm:items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#111827]">{convite.organization_name}</p>
                  <p className="text-xs text-[#6B7280]">
                    {rotuloPapel(convite.role)} · expira {formatarDataHoraSP(convite.expires_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    className="bg-[#3B5BDB] hover:bg-[#2d4cba] text-white"
                    disabled={aceitar.isPending}
                    onClick={() => aceitar.mutate(convite.id)}
                  >
                    Aceitar
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={recusar.isPending}
                    onClick={() => recusar.mutate(convite.id)}
                  >
                    Recusar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </SecaoShell>
  )
}
