import { api } from '#/lib/axios'
import type { NotificationPublica, NotificationsMarcadas } from './notifications.types'

export async function listarNotificacoes(
  somenteNaoLidas = false,
): Promise<NotificationPublica[]> {
  const { data } = await api.get<NotificationPublica[]>('/notifications', {
    params: somenteNaoLidas ? { somente_nao_lidas: true } : undefined,
  })
  return data
}

export async function marcarNotificacaoLida(id: string): Promise<NotificationPublica> {
  const { data } = await api.patch<NotificationPublica>(`/notifications/${id}`, {
    is_read: true,
  })
  return data
}

export async function marcarTodasNotificacoesLidas(): Promise<NotificationsMarcadas> {
  const { data } = await api.post<NotificationsMarcadas>('/notifications/marcar-lidas')
  return data
}
