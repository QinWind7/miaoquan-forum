<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/request'
import { useTheme } from '@/composables/useTheme'
import { useUserStore } from '@/stores/user'
import { clearRemembered, loadRemembered, saveRemembered } from '@/utils/remember'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { syncFromServer } = useTheme()

const account = ref('')
const password = ref('')
const rememberMe = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

// 下次打开登录页时自动回填上次记住的账号密码
onMounted(() => {
  const saved = loadRemembered()
  if (saved) {
    account.value = saved.account
    password.value = saved.password
    rememberMe.value = true
  }
})

async function onSubmit(): Promise<void> {
  errorMessage.value = ''

  if (!account.value.trim()) {
    errorMessage.value = '请填写用户名或邮箱'
    return
  }
  if (!password.value) {
    errorMessage.value = '请填写密码'
    return
  }

  submitting.value = true
  try {
    await userStore.login(account.value.trim(), password.value, rememberMe.value)

    // 勾选记住我 → 存本地；取消勾选 → 清掉旧记录
    if (rememberMe.value) {
      saveRemembered(account.value.trim(), password.value)
    } else {
      clearRemembered()
    }

    // 登录后拉取云端换肤偏好：有就覆盖本地，没有则保持现状
    await syncFromServer()
    const redirect = route.query.redirect as string | undefined
    router.replace(redirect || '/')
  } catch (error) {
    errorMessage.value = error instanceof ApiError ? error.message : '登录失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="onSubmit">
    <div>
      <label for="account" class="mb-1.5 block text-sm font-medium text-text">用户名或邮箱</label>
      <input
        id="account"
        v-model="account"
        type="text"
        autocomplete="username"
        placeholder="输入用户名或邮箱"
        class="cute-input"
      />
    </div>

    <div>
      <label for="password" class="mb-1.5 block text-sm font-medium text-text">密码</label>
      <input
        id="password"
        v-model="password"
        type="password"
        autocomplete="current-password"
        placeholder="输入密码"
        class="cute-input"
      />
    </div>

    <!-- 记住我：勾选后账号与密码存本地，下次打开自动填入 -->
    <label
      class="flex cursor-pointer items-center gap-2 rounded-2xl bg-surface-2 px-3 py-2.5 text-sm text-text transition hover:bg-primary-soft"
    >
      <input
        v-model="rememberMe"
        type="checkbox"
        class="h-4 w-4 shrink-0 accent-[var(--color-primary)]"
      />
      <span class="select-none">🐾 记住我</span>
      <span class="ml-auto text-[11px] text-text-muted">下次自动填入</span>
    </label>

    <p v-if="errorMessage" class="rounded-2xl bg-primary-soft px-4 py-2.5 text-sm text-text">
      😿 {{ errorMessage }}
    </p>

    <button
      type="submit"
      class="cute-btn w-full bg-primary py-2.5 font-semibold text-white hover:shadow-card disabled:opacity-60"
      :disabled="submitting"
    >
      {{ submitting ? '登录中…' : '登录' }}
    </button>

    <p class="text-center text-sm text-text-muted">
      还没有账号？
      <RouterLink to="/register" class="font-medium text-primary hover:underline">立即注册</RouterLink>
    </p>
  </form>
</template>
