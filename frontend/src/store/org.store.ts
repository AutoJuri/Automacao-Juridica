/**
 * A preferência de organização ativa é só UX.
 * Autorização continua no backend, a cada request, pela membership.
 */

import { create } from 'zustand'

const CHAVE_SESSAO = 'advogativa.org-ativa'

function lerSessao(): string | null {
  try {
    return sessionStorage.getItem(CHAVE_SESSAO)
  } catch {
    return null
  }
}

function gravarSessao(id: string | null): void {
  try {
    if (id) {
      sessionStorage.setItem(CHAVE_SESSAO, id)
    } else {
      sessionStorage.removeItem(CHAVE_SESSAO)
    }
  } catch {
    // Aba sem sessionStorage: o id segue só na memória desta sessão.
  }
}

interface OrgState {
  /** `null` é o contexto pessoal. Não autoriza acesso a nada. */
  activeOrganizationId: string | null
  setActiveOrganizationId: (id: string | null) => void
  clear: () => void
}

export const useOrgStore = create<OrgState>()((set) => ({
  activeOrganizationId: lerSessao(),
  setActiveOrganizationId: (id) => {
    gravarSessao(id)
    set({ activeOrganizationId: id })
  },
  clear: () => {
    gravarSessao(null)
    set({ activeOrganizationId: null })
  },
}))
