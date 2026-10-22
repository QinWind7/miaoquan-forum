<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { fetchMyLikes, likePost } from '@/api/post'
import type { LikedPost } from '@/api/types'
import Pagination from '@/components/common/Pagination.vue'
import PostCard from '@/components/post/PostCard.vue'
import { fromNow } from '@/utils/format'

const PAGE_SIZE = 10

const posts = ref<LikedPost[]>([])
const loading = ref(true)
const errorMessage = ref('')
const total = ref(0)
const page = ref(1)
const unlikingId = ref<number | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchMyLikes({ page: page.value, page_size: PAGE_SIZE })
    posts.value = data.results
    total.value = data.count
  } catch (error) {
    posts.value = []
    total.value = 0
    errorMessage.value = error instanceof Error ? error.message : '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

/** 列表内直接取消点赞：成功后把该帖从本页移除。 */
async function unlike(post: LikedPost): Promise<void> {
  if (unlikingId.value !== null) return
  unlikingId.value = post.id
  try {
    const result = await likePost(post.id)
    // 幂等切换：只有当结果确实变为未点赞时才移除
    if (!result.liked) {
      posts.value = posts.value.filter((item) => item.id !== post.id)
      total.value = Math.max(0, total.value - 1)
      if (posts.value.length === 0 && page.value > 1) page.value -= 1
    } else {
      post.is_liked = true
      post.like_count = result.like_count
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '取消点赞失败，请稍后重试'
  } finally {
    unlikingId.value = null
  }
}

watch(page, () => void load(), { immediate: true })
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="cute-card mb-4 flex items-center justify-between gap-3 p-4">
      <div>
        <h1 class="text-base font-bold text-text">💗 我点赞的帖子</h1>
        <p class="mt-0.5 text-xs text-text-muted">共 {{ total }} 篇，按点赞时间倒序</p>
      </div>
      <RouterLink
        :to="{ name: 'post-create' }"
        class="cute-btn shrink-0 bg-primary font-semibold text-white hover:shadow-card"
      >
        ✏️ 去发帖
      </RouterLink>
    </div>

    <p v-if="errorMessage" class="cute-card mb-4 px-4 py-2.5 text-sm text-text">😿 {{ errorMessage }}</p>

    <div v-if="loading" class="space-y-4">
      <div v-for="n in 3" :key="n" class="cute-card flex gap-4 p-4">
        <div class="h-24 w-24 shrink-0 animate-pulse rounded-2xl bg-surface-2 sm:h-28 sm:w-40" />
        <div class="flex-1 space-y-3 py-1">
          <div class="h-4 w-1/2 animate-pulse rounded-full bg-surface-2" />
          <div class="h-3 w-full animate-pulse rounded-full bg-surface-2" />
          <div class="h-3 w-2/3 animate-pulse rounded-full bg-surface-2" />
        </div>
      </div>
    </div>

    <div v-else-if="posts.length === 0" class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div class="text-5xl">💞</div>
      <p class="text-base font-semibold text-text">还没有点赞过任何帖子～</p>
      <p class="text-sm text-text-muted">看到喜欢的帖子，记得留下小心心哦！</p>
      <RouterLink
        :to="{ name: 'home' }"
        class="cute-btn mt-1 bg-primary font-semibold text-white hover:shadow-card"
      >
        🏠 去逛逛
      </RouterLink>
    </div>

    <template v-else>
      <div class="space-y-4">
        <PostCard v-for="post in posts" :key="post.id" :post="post">
          <template #extra>
            <div class="mt-2 flex items-center justify-between gap-2 border-t border-border pt-2">
              <span class="text-xs text-text-muted">💗 点赞于 {{ fromNow(post.liked_at) }}</span>
              <button
                type="button"
                class="rounded-full px-2 py-1 text-xs text-text-muted transition hover:bg-primary-soft hover:text-primary disabled:opacity-50"
                :disabled="unlikingId === post.id"
                @click="unlike(post)"
              >
                {{ unlikingId === post.id ? '处理中…' : '取消点赞' }}
              </button>
            </div>
          </template>
        </PostCard>
      </div>
      <Pagination :page="page" :total-pages="totalPages" @change="(value: number) => (page = value)" />
    </template>
  </div>
</template>
