import { queryOptions } from '@tanstack/react-query'

import { listarNotificacoes } from './notifications.api'
import { NOTIFICATIONS_POLL_MS, NOTIFICATIONS_QUERY_KEY } from './notifications.constants'

/** Lista do sino: uma query compartilhada (navbar + rail). Polling só
 * com a aba visível — `refetchIntervalInBackground: false`. */
export const notificacoesListQueryOptions = queryOptions({
  queryKey: NOTIFICATIONS_QUERY_KEY,
  queryFn: () => listarNotificacoes(false),
  refetchInterval: NOTIFICATIONS_POLL_MS,
  refetchIntervalInBackground: false,
})
