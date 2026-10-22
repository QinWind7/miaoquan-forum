import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { fetchUnreadSummary } from '@/api/notification'
import { useUserStore } from '@/stores/user'

/** 全局未读汇总：未读通知 + 未读私聊，由 App.vue 统一每 15 秒轮询。 */
export const useUnreadStore = defineStore('unread', () => {
  const notifications = ref(0)
  const messages = ref(0)
  const refreshing = ref(false)

  const total = computed(() => notifications.value + messages.value)

  let timer: ReturnType<typeof setInterval> | undefined

  async function refresh(): Promise<void> {
    if (!useUserStore().isLoggedIn) {
      reset()
      return
    }
    // 轮询与手动刷新可能重叠，只保留一次请求
    if (refreshing.value) return
    refreshing.value = true
    try {
      const data = await fetchUnreadSummary()
      notifications.value = data.notifications
      messages.value = data.messages
    } catch {
      // 未读数是辅助信息，失败保持上一次的值，不打扰用户
    } finally {
      refreshing.value = false
    }
  }

  function start(intervalMs = 15000): void {
    stop()
    void refresh()
    timer = setInterval(() => void refresh(), intervalMs)
  }

  function stop(): void {
    if (timer) {
      clearInterval(timer)
      timer = undefined
    }
  }

  function reset(): void {
    notifications.value = 0
    messages.value = 0
  }

  /** 本地立即减一，避免等下一轮轮询才更新红点。 */
  function decreaseNotifications(count = 1): void {
    notifications.value = Math.max(0, notifications.value - count)
  }

  function clearNotifications(): void {
    notifications.value = 0
  }

  return {
    notifications,
    messages,
    total,
    refreshing,
    refresh,
    start,
    stop,
    reset,
    decreaseNotifications,
    clearNotifications,
  }
})
