import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'

import { Button } from '#/components/ui/button'
import { AuthShell } from '#/features/auth/AuthShell'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import { useAuthStore } from '#/store/auth.store'
import { useOrgStore } from '#/store/org.store'
import { aceitarConvitePorToken, previewConvite, recusarConvitePorToken } from './organizations.api'
import { rotuloPapel } from './organizations.roles'

interface ConvitePageProps {
  token: string
}

export function ConvitePage({ token }: ConvitePageProps) {
  const navigate = useNavigate()
  const autenticado = useAuthStore((s) => s.isAuthenticated)
  const emailConta = useAuthStore((s) => s.user?.email)
  const setAtiva = useOrgStore((s) => s.setActiveOrganizationId)
  const destino = `/convite/${token}`

  const preview = useQuery({
    queryKey: ['organizations', 'invites', 'preview', token],
    queryFn: () => previewConvite(token),
    retry: false,
  })

  const aceitar = useMutation({
    mutationFn: () => aceitarConvitePorToken(token),
    onSuccess: (org) => {
      setAtiva(org.organization_id)
      void navigate({ to: '/organizacoes/$orgId', params: { orgId: org.organization_id } })
    },
  })

  const recusar = useMutation({
    mutationFn: () => recusarConvitePorToken(token),
    onSuccess: () => {
      void navigate({ to: '/' })
    },
  })

  const dados = preview.data
  const emailBate = dados && emailConta ? dados.email.toLowerCase() === emailConta.toLowerCase() : false

  return (
    <AuthShell>
      <div className="space-y-6">
        <header>
          <h1
            className="text-[2rem] leading-tight text-[#111827]"
            style={{ fontFamily: 'DM Serif Display, Georgia, serif' }}
          >
            Convite
          </h1>
          <p className="mt-2 text-sm text-[#6B7280]">
            Entre na organização com a conta do e-mail convidado.
          </p>
        </header>

        {preview.isLoading ? (
          <p className="text-sm text-[#6B7280]">Carregando convite...</p>
        ) : preview.isError || !dados ? (
          <p className="text-sm text-[#991B1B]">Este convite não está mais válido.</p>
        ) : (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 space-y-2">
            <p className="text-base font-semibold text-[#111827]">{dados.organization_name}</p>
            <p className="text-sm text-[#374151]">Papel: {rotuloPapel(dados.role)}</p>
            <p className="text-sm text-[#374151]">E-mail: {dados.email}</p>
            <p className="text-xs text-[#6B7280]">Expira {formatarDataHoraSP(dados.expires_at)}</p>
          </div>
        )}

        {dados && !autenticado ? (
          <div className="flex flex-col gap-2">
            <Button asChild className="bg-[#3B5BDB] hover:bg-[#2d4cba] text-white">
              <Link to="/login" search={{ redirect: destino, email: dados.email, mode: 'register' }}>
                Criar conta
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/login" search={{ redirect: destino, mode: 'login' }}>
                Entrar
              </Link>
            </Button>
          </div>
        ) : null}

        {dados && autenticado && emailBate ? (
          <div className="flex gap-2">
            <Button
              type="button"
              className="bg-[#3B5BDB] hover:bg-[#2d4cba] text-white"
              disabled={aceitar.isPending}
              onClick={() => aceitar.mutate()}
            >
              Aceitar
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={recusar.isPending}
              onClick={() => recusar.mutate()}
            >
              Recusar
            </Button>
          </div>
        ) : null}

        {dados && autenticado && !emailBate ? (
          <p className="text-sm text-[#991B1B]">
            Este convite é para {dados.email}. Entre com essa conta para aceitar.
          </p>
        ) : null}

        {aceitar.isError ? (
          <p className="text-xs text-[#DC2626]">
            {mensagemDeErro(aceitar.error, {
              400: 'Este convite não está mais válido.',
              403: 'Este convite não é para a conta em que você entrou.',
              409: 'Você já faz parte desta organização.',
            })}
          </p>
        ) : null}
      </div>
    </AuthShell>
  )
}
