import request from './request'
import type { NotificationItem, NotificationType, Paginated } from './types'

/** 我的通知列表（分页，默认按时间倒序）。 */
export async function fetchNotifications(params: {
  is_read?: boolean
  type?: NotificationType
  page?: number
  page_size?: number
} = {}): Promise<Paginated<NotificationItem>> {
  const { data } = await request.get<Paginated<NotificationItem>>('/notifications/', { params })
  return data
}

export interface UnreadSummary {
  notifications: number
  messages: number
  total: number
}

/** 未读汇总（通知 + 私聊），供全局每 15 秒轮询铃铛红点。 */
export async function fetchUnreadSummary(): Promise<UnreadSummary> {
  const { data } = await request.get<UnreadSummary>('/notifications/unread-summary/')
  return data
}

export async function markNotificationRead(id: number): Promise<NotificationItem> {
  const { data } = await request.post<NotificationItem>(`/notifications/${id}/read/`)
  return data
}

export async function markAllNotificationsRead(): Promise<number> {
  const { data } = await request.post<{ updated: number }>('/notifications/read-all/')
  return data.updated
}

/** 清除当前用户所有已读通知，返回删除条数。 */
export async function deleteReadNotifications(): Promise<number> {
  const { data } = await request.delete<{ deleted: number }>('/notifications/read/')
  return data.deleted
}
