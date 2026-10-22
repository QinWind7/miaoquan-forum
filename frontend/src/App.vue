<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from 'vue'

import { useTheme } from '@/composables/useTheme'
import { useUnreadStore } from '@/stores/unread'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const unreadStore = useUnreadStore()
const { syncFromServer } = useTheme()

// 登录后每 15 秒拉一次未读总数；退出登录立即停止并清零
watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) {
      unreadStore.start(15000)
    } else {
      unreadStore.stop()
      unreadStore.reset()
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (!userStore.isLoggedIn) return
  try {
    // 刷新一次用户资料（等级 / 头像等），再拉取云端换肤偏好
    await userStore.fetchMe()
  } catch {
    // token 失效的情况由请求拦截器统一处理，这里不阻断首屏渲染
  }
  await syncFromServer()
})

onBeforeUnmount(() => {
  unreadStore.stop()
})
</script>

<template>
  <router-view />
</template>
