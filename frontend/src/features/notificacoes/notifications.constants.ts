export const NOTIFICATIONS_QUERY_KEY = ['notifications'] as const

/** Intervalo do polling do sino — o ciclo e-SAJ é de 10 min; isto só
 * atualiza o badge sem o advogado recarregar a página. Sem WebSocket. */
export const NOTIFICATIONS_POLL_MS = 60_000
