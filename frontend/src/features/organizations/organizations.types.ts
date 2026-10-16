import type { PapelConvidavel, PapelOrg } from './organizations.roles'

export interface OrganizationMine {
  id: string
  name: string
  slug: string
  role: PapelOrg
}

export interface OrganizationDetail extends OrganizationMine {
  created_at: string
}

export interface MemberPublic {
  id: string
  name: string
  email: string
  role: PapelOrg
  joined_at: string
}

export interface InvitePending {
  id: string
  email: string
  role: PapelConvidavel
  expires_at: string
  created_at: string
}

export interface InviteReceived {
  id: string
  organization_name: string
  role: PapelConvidavel
  expires_at: string
  created_at: string
}

export interface InvitePreview {
  organization_name: string
  role: PapelConvidavel
  email: string
  expires_at: string
}

export interface InviteAccepted {
  organization_id: string
  name: string
  slug: string
  role: PapelOrg
}
