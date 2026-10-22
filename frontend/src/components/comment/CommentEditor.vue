<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { createComment } from '@/api/comment'
import { ApiError } from '@/api/request'
import type { Comment, UserBrief } from '@/api/types'
import { useUserStore } from '@/stores/user'

const MAX_LENGTH = 1000

const props = withDefaults(
  defineProps<{
    postId: number
    parentId?: number
    replyToUser?: UserBrief | null
    placeholder?: string
  }>(),
  { parentId: undefined, replyToUser: null, placeholder: '' },
)

const emit = defineEmits<{
  (e: 'submitted', comment: Comment): void
  (e: 'cancel'): void
}>()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const content = ref('')
const submitting = ref(false)
const errorMessage = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)

const avatarText = computed(() => (userStore.displayName || '喵').slice(0, 1))
const isReply = computed(() => props.parentId !== undefined)
const tip = computed(
  () =>
    props.placeholder ||
    (props.replyToUser ? `回复 @${props.replyToUser.display_name}` : '说点什么吧，友善交流哦～'),
)

onMounted(() => {
  nextTick(() => inputRef.value?.focus())
})

async function onSubmit(): Promise<void> {
  errorMessage.value = ''

  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  const text = content.value.trim()
  if (!text) {
    errorMessage.value = '评论内容不能为空哦～'
    return
  }
  if (text.length > MAX_LENGTH) {
    errorMessage.value = `评论最多 ${MAX_LENGTH} 字哦～`
    return
  }

  submitting.value = true
  try {
    const comment = await createComment(props.postId, { content: text, parent: props.parentId })
    content.value = ''
    emit('submitted', comment)
  } catch (error) {
    errorMessage.value = error instanceof ApiError ? error.message : '评论发送失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex gap-3">
    <img
      v-if="userStore.avatar"
      :src="userStore.avatar"
      :alt="userStore.displayName"
      class="h-9 w-9 shrink-0 rounded-full object-cover"
    />
    <span
      v-else
      class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary-soft text-sm font-bold text-text"
    >
      {{ avatarText }}
    </span>

    <div class="min-w-0 flex-1">
      <p class="mb-1.5 text-xs text-text-muted">{{ tip }}</p>
      <textarea
        ref="inputRef"
        v-model="content"
        rows="3"
        :maxlength="MAX_LENGTH"
        :placeholder="tip"
        class="cute-input resize-none"
      />
      <p v-if="errorMessage" class="mt-1.5 text-xs text-primary">😿 {{ errorMessage }}</p>
      <div class="mt-2 flex items-center justify-between gap-2">
        <span class="text-[11px] text-text-muted">{{ content.length }} / {{ MAX_LENGTH }}</span>
        <div class="flex items-center gap-2">
          <button
            v-if="isReply"
            type="button"
            class="cute-btn border border-border bg-surface text-text hover:shadow-card"
            :disabled="submitting"
            @click="emit('cancel')"
          >
            取消
          </button>
          <button
            type="button"
            class="cute-btn bg-primary font-semibold text-white hover:shadow-card disabled:opacity-60"
            :disabled="submitting"
            @click="onSubmit"
          >
            {{ submitting ? '发送中…' : isReply ? '回复' : '发布评论' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
