import type { QueryClient } from '@tanstack/react-query'

import { NOTIFICATIONS_QUERY_KEY } from '#/features/notificacoes/notifications.constants'
import { PROCESSOS_QUERY_KEY } from '#/features/processos/processos.constants'
import { CREDENTIALS_STATUS_QUERY_KEY } from '#/features/settings/credentials.constants'

/** Limpa o cache da sessão autenticada (logout e refresh expirado). */
export function limparQueriesDaSessao(client: QueryClient): void {
  client.removeQueries({ queryKey: CREDENTIALS_STATUS_QUERY_KEY })
  client.removeQueries({ queryKey: PROCESSOS_QUERY_KEY })
  client.removeQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
}
