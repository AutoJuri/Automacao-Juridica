/**
 * Contratos das notificações in-app, espelhando
 * `backend/app/schemas/notification.py`.
 */

export type NotificationTipo =
  | 'movimentacao'
  | 'intimacao'
  | 'audiencia'
  | 'sistema'
  | 'convite_org'
  | 'task_atribuida'
  | 'task_concluida'

export interface NotificationPublica {
  id: string
  processo_id: string | null
  task_id: string | null
  organization_id: string | null
  tipo: NotificationTipo | string
  titulo: string
  message: string
  is_read: boolean
  created_at: string
}

export interface NotificationsMarcadas {
  marcadas: number
}
