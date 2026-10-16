import type { QueryClient } from '@tanstack/react-query'

import { NOTIFICATIONS_QUERY_KEY } from '#/features/notificacoes/notifications.constants'
import { ORGANIZATIONS_QUERY_KEY } from '#/features/organizations/organizations.constants'
import {
  AUDIENCIAS_QUERY_KEY,
  INTIMACOES_QUERY_KEY,
  PROCESSOS_QUERY_KEY,
} from '#/features/processos/processos.constants'
import { CREDENTIALS_STATUS_QUERY_KEY } from '#/features/settings/credentials.constants'
import { DRIVE_QUERY_KEY } from '#/features/drive/drive.constants'
import { ELABORACOES_QUERY_KEY } from '#/features/elaboracao/elaboracoes.constants'
import { TAREFAS_QUERY_KEY } from '#/features/tarefas/tarefas.constants'
import { useOrgStore } from '#/store/org.store'

/** Limpa o cache da sessão autenticada (logout e refresh expirado). */
export function limparQueriesDaSessao(client: QueryClient): void {
  client.removeQueries({ queryKey: CREDENTIALS_STATUS_QUERY_KEY })
  client.removeQueries({ queryKey: PROCESSOS_QUERY_KEY })
  client.removeQueries({ queryKey: INTIMACOES_QUERY_KEY })
  client.removeQueries({ queryKey: AUDIENCIAS_QUERY_KEY })
  client.removeQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
  client.removeQueries({ queryKey: ORGANIZATIONS_QUERY_KEY })
  client.removeQueries({ queryKey: TAREFAS_QUERY_KEY })
  client.removeQueries({ queryKey: ELABORACOES_QUERY_KEY })
  client.removeQueries({ queryKey: DRIVE_QUERY_KEY })
  useOrgStore.getState().clear()
}
