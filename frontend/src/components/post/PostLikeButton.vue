<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

import { likePost } from '@/api/post'
import { useUserStore } from '@/stores/user'
import { compactCount } from '@/utils/format'

/** 只需要这三个字段即可工作，PostCard 与详情页共用同一份实现。 */
interface LikeTarget {
  id: number
  is_liked: boolean
  like_count: number
}

const props = defineProps<{ post: LikeTarget }>()

const userStore = useUserStore()
const liking = ref(false)
const showLoginTip = ref(false)
let tipTimer: ReturnType<typeof setTimeout> | undefined

async function toggleLike(): Promise<void> {
  // 未登录：明确提示，不静默失败
  if (!userStore.isLoggedIn) {
    showLoginTip.value = true
    if (tipTimer) clearTimeout(tipTimer)
    tipTimer = setTimeout(() => {
      showLoginTip.value = false
    }, 2800)
    return
  }

  if (liking.value) return
  liking.value = true

  const target = props.post
  const prevLiked = target.is_liked
  const prevCount = target.like_count
  // 乐观更新，失败再回滚
  target.is_liked = !prevLiked
  target.like_count = prevCount + (prevLiked ? -1 : 1)

  try {
    const result = await likePost(target.id)
    target.is_liked = result.liked
    target.like_count = result.like_count
  } catch {
    target.is_liked = prevLiked
    target.like_count = prevCount
  } finally {
    liking.value = false
  }
}
</script>

<template>
  <div class="relative shrink-0">
    <button
      type="button"
      class="flex items-center gap-1 rounded-full px-2 py-1 text-xs transition hover:bg-primary-soft"
      :class="post.is_liked ? 'font-semibold text-primary' : 'text-text-muted'"
      @click="toggleLike"
    >
      <span>{{ post.is_liked ? '💗' : '🤍' }}</span>
      <span>{{ compactCount(post.like_count) }}</span>
    </button>
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 translate-y-1"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="showLoginTip"
        class="absolute bottom-full right-0 z-10 mb-1 w-max rounded-xl border border-border bg-surface px-3 py-1.5 text-[11px] text-text shadow-card"
      >
        登录后才能点赞哦，
        <RouterLink to="/login" class="text-primary underline">去登录 →</RouterLink>
      </div>
    </Transition>
  </div>
</template>
