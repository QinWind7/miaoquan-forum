import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authApi from '@/api/auth'
import type { RegisterPayload } from '@/api/auth'
import type { User } from '@/api/types'

export const useUserStore = defineStore(
  'user',
  () => {
    const access = ref('')
    const refresh = ref('')
    const user = ref<User | null>(null)

    const isLoggedIn = computed(() => Boolean(access.value))
    const displayName = computed(() => user.value?.display_name || user.value?.username || '')
    const avatar = computed(() => user.value?.avatar ?? null)

    function setTokens(nextAccess: string, nextRefresh: string): void {
      access.value = nextAccess
      refresh.value = nextRefresh
    }

    function setUser(nextUser: User | null): void {
      user.value = nextUser
    }

    function clear(): void {
      access.value = ''
      refresh.value = ''
      user.value = null
    }

    async function login(
      account: string,
      password: string,
      rememberMe = false,
    ): Promise<User> {
      const data = await authApi.login(account, password, rememberMe)
      setTokens(data.access, data.refresh)
      setUser(data.user)
      return data.user
    }

    async function register(payload: RegisterPayload): Promise<User> {
      const data = await authApi.register(payload)
      setTokens(data.access, data.refresh)
      setUser(data.user)
      return data.user
    }

    async function fetchMe(): Promise<User> {
      const data = await authApi.me()
      setUser(data)
      return data
    }

    async function logout(): Promise<void> {
      try {
        if (refresh.value) await authApi.logout(refresh.value)
      } catch {
        // 后端登出失败（如 token 已失效）不阻塞本地清理
      }
      clear()
    }

    return {
      access,
      refresh,
      user,
      isLoggedIn,
      displayName,
      avatar,
      setTokens,
      setUser,
      clear,
      login,
      register,
      fetchMe,
      logout,
    }
  },
  { persist: { key: 'user' } },
)
