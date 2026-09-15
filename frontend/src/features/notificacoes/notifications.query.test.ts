import { describe, expect, it } from 'vitest'

import { NOTIFICATIONS_POLL_MS, NOTIFICATIONS_QUERY_KEY } from './notifications.constants'
import { notificacoesListQueryOptions } from './notifications.query'

describe('notificacoesListQueryOptions', () => {
  it('reusa a chave do sino e faz polling só com a aba visível', () => {
    expect(notificacoesListQueryOptions.queryKey).toEqual(NOTIFICATIONS_QUERY_KEY)
    expect(notificacoesListQueryOptions.refetchInterval).toBe(NOTIFICATIONS_POLL_MS)
    expect(notificacoesListQueryOptions.refetchIntervalInBackground).toBe(false)
    expect(NOTIFICATIONS_POLL_MS).toBe(60_000)
  })
})
