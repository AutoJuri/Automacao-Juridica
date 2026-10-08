export const ORGANIZATIONS_QUERY_KEY = ['organizations'] as const

export function orgDetailKey(orgId: string) {
  return ['organizations', orgId] as const
}

export function orgMembersKey(orgId: string) {
  return ['organizations', orgId, 'members'] as const
}

export function orgInvitesKey(orgId: string) {
  return ['organizations', orgId, 'invites'] as const
}

export const RECEIVED_INVITES_QUERY_KEY = ['organizations', 'invites', 'received'] as const
