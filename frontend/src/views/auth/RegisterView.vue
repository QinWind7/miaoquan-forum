<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import type { RegisterPayload } from '@/api/auth'
import { ApiError } from '@/api/request'
import { useTheme } from '@/composables/useTheme'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const { syncFromServer } = useTheme()

const username = ref('')
const email = ref('')
const nickname = ref('')
const password = ref('')
const password2 = ref('')
const submitting = ref(false)
const errorMessage = ref('')

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

async function onSubmit(): Promise<void> {
  errorMessage.value = ''

  if (!username.value.trim()) {
    errorMessage.value = '请填写用户名'
    return
  }
  if (email.value && !EMAIL_RE.test(email.value.trim())) {
    errorMessage.value = '邮箱格式看起来不太对哦'
    return
  }
  if (!password.value) {
    errorMessage.value = '请填写密码'
    return
  }
  if (password.value.length < 8) {
    errorMessage.value = '密码至少需要 8 位'
    return
  }
  if (password.value !== password2.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  const payload: RegisterPayload = {
    username: username.value.trim(),
    password: password.value,
    password2: password2.value,
  }
  if (email.value.trim()) payload.email = email.value.trim()
  if (nickname.value.trim()) payload.nickname = nickname.value.trim()

  submitting.value = true
  try {
    await userStore.register(payload)
    await syncFromServer()
    router.replace('/')
  } catch (error) {
    errorMessage.value = error instanceof ApiError ? error.message : '注册失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="onSubmit">
    <div>
      <label for="username" class="mb-1.5 block text-sm font-medium text-text">
        用户名 <span class="text-primary">*</span>
      </label>
      <input
        id="username"
        v-model="username"
        type="text"
        autocomplete="username"
        placeholder="登录时使用，必填"
        class="cute-input"
      />
    </div>

    <div>
      <label for="email" class="mb-1.5 block text-sm font-medium text-text">邮箱（可留空）</label>
      <input
        id="email"
        v-model="email"
        type="email"
        autocomplete="email"
        placeholder="可用于登录，可留空"
        class="cute-input"
      />
    </div>

    <div>
      <label for="nickname" class="mb-1.5 block text-sm font-medium text-text">昵称（可留空）</label>
      <input
        id="nickname"
        v-model="nickname"
        type="text"
        placeholder="展示给其他小伙伴的名字，可留空"
        class="cute-input"
      />
      <p class="mt-1 text-xs text-text-muted">昵称与邮箱可留空，留空时会用用户名显示。</p>
    </div>

    <div>
      <label for="password" class="mb-1.5 block text-sm font-medium text-text">
        密码 <span class="text-primary">*</span>
      </label>
      <input
        id="password"
        v-model="password"
        type="password"
        autocomplete="new-password"
        placeholder="至少 8 位"
        class="cute-input"
      />
    </div>

    <div>
      <label for="password2" class="mb-1.5 block text-sm font-medium text-text">
        确认密码 <span class="text-primary">*</span>
      </label>
      <input
        id="password2"
        v-model="password2"
        type="password"
        autocomplete="new-password"
        placeholder="再输入一次密码"
        class="cute-input"
      />
    </div>

    <p v-if="errorMessage" class="rounded-2xl bg-primary-soft px-4 py-2.5 text-sm text-text">
      😿 {{ errorMessage }}
    </p>

    <button
      type="submit"
      class="cute-btn w-full bg-primary py-2.5 font-semibold text-white hover:shadow-card disabled:opacity-60"
      :disabled="submitting"
    >
      {{ submitting ? '注册中…' : '注册并进入喵圈' }}
    </button>

    <p class="text-center text-sm text-text-muted">
      已经有账号了？
      <RouterLink to="/login" class="font-medium text-primary hover:underline">去登录</RouterLink>
    </p>
  </form>
</template>
