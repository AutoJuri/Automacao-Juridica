import { api } from '#/lib/axios'
import type { PapelConvidavel } from './organizations.roles'
import type {
  InviteAccepted,
  InvitePending,
  InvitePreview,
  InviteReceived,
  MemberPublic,
  OrganizationDetail,
  OrganizationMine,
} from './organizations.types'

export async function listarOrganizacoes(): Promise<OrganizationMine[]> {
  const { data } = await api.get<OrganizationMine[]>('/organizations')
  return data
}

export async function criarOrganizacao(name: string): Promise<OrganizationDetail> {
  const { data } = await api.post<OrganizationDetail>('/organizations', { name })
  return data
}

export async function buscarOrganizacao(orgId: string): Promise<OrganizationDetail> {
  const { data } = await api.get<OrganizationDetail>(`/organizations/${orgId}`)
  return data
}

export async function renomearOrganizacao(orgId: string, name: string): Promise<OrganizationDetail> {
  const { data } = await api.patch<OrganizationDetail>(`/organizations/${orgId}`, { name })
  return data
}

export async function excluirOrganizacao(orgId: string): Promise<void> {
  await api.delete(`/organizations/${orgId}`)
}

export async function listarMembros(orgId: string): Promise<MemberPublic[]> {
  const { data } = await api.get<MemberPublic[]>(`/organizations/${orgId}/members`)
  return data
}

export async function alterarPapel(
  orgId: string,
  memberId: string,
  role: PapelConvidavel,
): Promise<MemberPublic> {
  const { data } = await api.patch<MemberPublic>(`/organizations/${orgId}/members/${memberId}`, {
    role,
  })
  return data
}

export async function removerMembro(orgId: string, memberId: string): Promise<void> {
  await api.delete(`/organizations/${orgId}/members/${memberId}`)
}

export async function transferirOwnership(orgId: string, memberId: string): Promise<void> {
  await api.post(`/organizations/${orgId}/members/${memberId}/transfer-ownership`)
}

export async function listarConvites(orgId: string): Promise<InvitePending[]> {
  const { data } = await api.get<InvitePending[]>(`/organizations/${orgId}/invites`)
  return data
}

export async function convidar(
  orgId: string,
  email: string,
  role: PapelConvidavel,
): Promise<InvitePending> {
  const { data } = await api.post<InvitePending>(`/organizations/${orgId}/invites`, { email, role })
  return data
}

export async function cancelarConvite(orgId: string, inviteId: string): Promise<void> {
  await api.delete(`/organizations/${orgId}/invites/${inviteId}`)
}

export async function listarConvitesRecebidos(): Promise<InviteReceived[]> {
  const { data } = await api.get<InviteReceived[]>('/organizations/invites/received')
  return data
}

export async function aceitarConviteRecebido(inviteId: string): Promise<InviteAccepted> {
  const { data } = await api.post<InviteAccepted>(
    `/organizations/invites/received/${inviteId}/accept`,
  )
  return data
}

export async function recusarConviteRecebido(inviteId: string): Promise<void> {
  await api.post(`/organizations/invites/received/${inviteId}/decline`)
}

export async function previewConvite(token: string): Promise<InvitePreview> {
  const { data } = await api.get<InvitePreview>(`/organizations/invites/${token}`)
  return data
}

export async function aceitarConvitePorToken(token: string): Promise<InviteAccepted> {
  const { data } = await api.post<InviteAccepted>(`/organizations/invites/${token}/accept`)
  return data
}

export async function recusarConvitePorToken(token: string): Promise<void> {
  await api.post(`/organizations/invites/${token}/decline`)
}
