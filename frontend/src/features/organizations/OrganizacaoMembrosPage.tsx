import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'

import { Button } from '#/components/ui/button'
import { Input } from '#/components/ui/input'
import { Label } from '#/components/ui/label'
import { mensagemDeErro } from '#/features/auth/auth.errors'
import { SecaoShell } from '#/features/secoes/SecaoShell'
import { formatarDataHoraSP } from '#/features/processos/processos.dates'
import { useAuthStore } from '#/store/auth.store'
import { useOrgStore } from '#/store/org.store'
import {
  alterarPapel,
  buscarOrganizacao,
  cancelarConvite,
  convidar,
  excluirOrganizacao,
  listarConvites,
  listarMembros,
  removerMembro,
  renomearOrganizacao,
  transferirOwnership,
} from './organizations.api'
import {
  ORGANIZATIONS_QUERY_KEY,
  orgDetailKey,
  orgInvitesKey,
  orgMembersKey,
} from './organizations.constants'
import { PAPEIS_CONVIDAVEIS, ehOwner, podeGerenciar, rotuloPapel, type PapelConvidavel } from './organizations.roles'

interface OrganizacaoMembrosPageProps {
  orgId: string
}

export function OrganizacaoMembrosPage({ orgId }: OrganizacaoMembrosPageProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const emailAtual = useAuthStore((s) => s.user?.email)
  const setAtiva = useOrgStore((s) => s.setActiveOrganizationId)
  const [nome, setNome] = useState('')
  const [emailConvite, setEmailConvite] = useState('')
  const [papelConvite, setPapelConvite] = useState<PapelConvidavel>('advogado')
  const [confirmacaoExcluir, setConfirmacaoExcluir] = useState('')
  const [transferirPara, setTransferirPara] = useState('')

  const detalhe = useQuery({
    queryKey: orgDetailKey(orgId),
    queryFn: () => buscarOrganizacao(orgId),
  })

  const gestor = podeGerenciar(detalhe.data?.role)
  const dono = ehOwner(detalhe.data?.role)

  const membros = useQuery({
    queryKey: orgMembersKey(orgId),
    queryFn: () => listarMembros(orgId),
    enabled: detalhe.isSuccess,
  })

  const convites = useQuery({
    queryKey: orgInvitesKey(orgId),
    queryFn: () => listarConvites(orgId),
    enabled: gestor,
  })

  useEffect(() => {
    if (detalhe.data) {
      setAtiva(orgId)
      setNome(detalhe.data.name)
    }
  }, [detalhe.data, orgId, setAtiva])

  function invalidar() {
    void queryClient.invalidateQueries({ queryKey: ORGANIZATIONS_QUERY_KEY })
    void queryClient.invalidateQueries({ queryKey: orgDetailKey(orgId) })
    void queryClient.invalidateQueries({ queryKey: orgMembersKey(orgId) })
    void queryClient.invalidateQueries({ queryKey: orgInvitesKey(orgId) })
  }

  const salvarNome = useMutation({
    mutationFn: () => renomearOrganizacao(orgId, nome.trim()),
    onSuccess: invalidar,
  })

  const enviarConvite = useMutation({
    mutationFn: () => convidar(orgId, emailConvite.trim(), papelConvite),
    onSuccess: () => {
      setEmailConvite('')
      invalidar()
    },
  })

  const mudarPapel = useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: PapelConvidavel }) =>
      alterarPapel(orgId, memberId, role),
    onSuccess: invalidar,
  })

  const remover = useMutation({
    mutationFn: (memberId: string) => removerMembro(orgId, memberId),
    onSuccess: (_data, memberId) => {
      const saiu = membros.data?.find((m) => m.id === memberId)?.email === emailAtual
      invalidar()
      if (saiu) {
        setAtiva(null)
        void navigate({ to: '/' })
      }
    },
  })

  const transferir = useMutation({
    mutationFn: () => transferirOwnership(orgId, transferirPara),
    onSuccess: () => {
      setTransferirPara('')
      invalidar()
    },
  })

  const excluir = useMutation({
    mutationFn: () => excluirOrganizacao(orgId),
    onSuccess: () => {
      setAtiva(null)
      void queryClient.invalidateQueries({ queryKey: ORGANIZATIONS_QUERY_KEY })
      void navigate({ to: '/' })
    },
  })

  const cancelar = useMutation({
    mutationFn: (inviteId: string) => cancelarConvite(orgId, inviteId),
    onSuccess: invalidar,
  })

  if (detalhe.isError) {
    return (
      <SecaoShell>
        <p className="text-sm text-[#6B7280]">Você não tem acesso a esta organização.</p>
      </SecaoShell>
    )
  }

  const org = detalhe.data
  const outros = (membros.data ?? []).filter((m) => m.role !== 'owner')

  return (
    <SecaoShell>
      <div className="max-w-3xl mx-auto w-full space-y-6">
        <header className="space-y-1">
          <p className="text-[11px] font-medium tracking-[0.16em] uppercase text-[#6B7280]">
            Organização
          </p>
          <h1 className="text-2xl font-semibold text-[#111827]">{org?.name ?? 'Carregando...'}</h1>
          {org ? (
            <p className="text-sm text-[#6B7280]">
              {rotuloPapel(org.role)} · {org.slug}
            </p>
          ) : null}
        </header>

        {gestor && org ? (
          <section className="rounded-xl border border-[#E5E7EB] bg-white p-4 space-y-3">
            <h2 className="text-sm font-semibold text-[#111827]">Nome</h2>
            <form
              className="flex flex-col sm:flex-row gap-2"
              onSubmit={(evento) => {
                evento.preventDefault()
                if (nome.trim().length >= 2 && nome.trim() !== org.name) {
                  salvarNome.mutate()
                }
              }}
            >
              <Input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={255} />
              <Button
                type="submit"
                disabled={salvarNome.isPending || nome.trim().length < 2 || nome.trim() === org.name}
                className="bg-[#3B5BDB] hover:bg-[#2d4cba] text-white"
              >
                Salvar
              </Button>
            </form>
          </section>
        ) : null}

        <section className="rounded-xl border border-[#E5E7EB] bg-white p-4 space-y-3">
          <h2 className="text-sm font-semibold text-[#111827]">Membros</h2>
          <ul className="divide-y divide-[#F3F4F6]">
            {(membros.data ?? []).map((membro) => {
              const souEu = membro.email === emailAtual
              const podeMudarPapel = gestor && membro.role !== 'owner'
              const podeRemover = membro.role !== 'owner' && (gestor || souEu)
              return (
                <li key={membro.id} className="py-3 flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-[#111827] truncate">
                      {membro.name}
                      {souEu ? ' (você)' : ''}
                    </p>
                    <p className="text-xs text-[#6B7280] truncate">{membro.email}</p>
                  </div>
                  {podeMudarPapel ? (
                    <select
                      aria-label={`Papel de ${membro.name}`}
                      value={membro.role}
                      onChange={(evento) =>
                        mudarPapel.mutate({
                          memberId: membro.id,
                          role: evento.target.value as PapelConvidavel,
                        })
                      }
                      className="h-9 rounded-md border border-[#E5E7EB] bg-white px-2 text-sm"
                    >
                      {PAPEIS_CONVIDAVEIS.map((papel) => (
                        <option key={papel} value={papel}>
                          {rotuloPapel(papel)}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="text-xs font-medium text-[#374151]">{rotuloPapel(membro.role)}</span>
                  )}
                  {podeRemover ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => remover.mutate(membro.id)}
                    >
                      {souEu ? 'Sair' : 'Remover'}
                    </Button>
                  ) : null}
                </li>
              )
            })}
          </ul>
        </section>

        {gestor ? (
          <section className="rounded-xl border border-[#E5E7EB] bg-white p-4 space-y-3">
            <h2 className="text-sm font-semibold text-[#111827]">Convidar</h2>
            <p className="text-xs text-[#6B7280]">
              Em development o link do convite aparece no log da API. Se a pessoa já tiver conta, ela
              também recebe um aviso no sino.
            </p>
            <form
              className="grid gap-3 sm:grid-cols-[1fr_160px_auto] sm:items-end"
              onSubmit={(evento) => {
                evento.preventDefault()
                enviarConvite.mutate()
              }}
            >
              <div className="space-y-1">
                <Label htmlFor="convite-email">E-mail</Label>
                <Input
                  id="convite-email"
                  type="email"
                  required
                  value={emailConvite}
                  onChange={(e) => setEmailConvite(e.target.value)}
                  placeholder="colega@escritorio.com"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="convite-papel">Papel</Label>
                <select
                  id="convite-papel"
                  value={papelConvite}
                  onChange={(e) => setPapelConvite(e.target.value as PapelConvidavel)}
                  className="h-9 w-full rounded-md border border-[#E5E7EB] bg-white px-2 text-sm"
                >
                  {PAPEIS_CONVIDAVEIS.map((papel) => (
                    <option key={papel} value={papel}>
                      {rotuloPapel(papel)}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                type="submit"
                disabled={enviarConvite.isPending || emailConvite.trim().length === 0}
                className="bg-[#3B5BDB] hover:bg-[#2d4cba] text-white"
              >
                Convidar
              </Button>
            </form>
            {enviarConvite.isError ? (
              <p className="text-xs text-[#DC2626]">
                {mensagemDeErro(enviarConvite.error, {
                  403: 'Você não pode convidar membros.',
                  409: 'Este e-mail já é membro da organização.',
                  422: 'Confira o e-mail e o papel.',
                })}
              </p>
            ) : null}

            <ul className="divide-y divide-[#F3F4F6]">
              {(convites.data ?? []).map((convite) => (
                <li key={convite.id} className="py-3 flex items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-[#111827] truncate">{convite.email}</p>
                    <p className="text-xs text-[#6B7280]">
                      {rotuloPapel(convite.role)} · expira {formatarDataHoraSP(convite.expires_at)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => cancelar.mutate(convite.id)}
                  >
                    Cancelar
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {dono && org ? (
          <section className="rounded-xl border border-[#E5E7EB] bg-white p-4 space-y-4">
            <h2 className="text-sm font-semibold text-[#111827]">Ownership</h2>
            <form
              className="flex flex-col sm:flex-row gap-2"
              onSubmit={(evento) => {
                evento.preventDefault()
                if (transferirPara) {
                  transferir.mutate()
                }
              }}
            >
              <select
                aria-label="Novo owner"
                value={transferirPara}
                onChange={(e) => setTransferirPara(e.target.value)}
                className="h-9 flex-1 rounded-md border border-[#E5E7EB] bg-white px-2 text-sm"
              >
                <option value="">Transferir para...</option>
                {outros.map((membro) => (
                  <option key={membro.id} value={membro.id}>
                    {membro.name}
                  </option>
                ))}
              </select>
              <Button type="submit" variant="outline" disabled={!transferirPara || transferir.isPending}>
                Transferir
              </Button>
            </form>

            <form
              className="space-y-2 border-t border-[#F3F4F6] pt-4"
              onSubmit={(evento) => {
                evento.preventDefault()
                if (confirmacaoExcluir === org.name) {
                  excluir.mutate()
                }
              }}
            >
              <p className="text-xs text-[#6B7280]">
                Para excluir, digite o nome da organização: {org.name}
              </p>
              <Input
                value={confirmacaoExcluir}
                onChange={(e) => setConfirmacaoExcluir(e.target.value)}
                aria-label="Confirmar nome para excluir"
              />
              <Button
                type="submit"
                variant="outline"
                disabled={confirmacaoExcluir !== org.name || excluir.isPending}
                className="text-[#DC2626] border-[#FECACA] hover:bg-[#FEF2F2]"
              >
                Excluir organização
              </Button>
            </form>
          </section>
        ) : null}
      </div>
    </SecaoShell>
  )
}
