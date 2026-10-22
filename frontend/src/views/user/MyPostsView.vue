<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { fetchMyPosts } from '@/api/post'
import type { Post } from '@/api/types'
import Pagination from '@/components/common/Pagination.vue'
import PostCard from '@/components/post/PostCard.vue'

const PAGE_SIZE = 10

const posts = ref<Post[]>([])
const loading = ref(true)
const errorMessage = ref('')
const total = ref(0)
const page = ref(1)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchMyPosts({ page: page.value, page_size: PAGE_SIZE })
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

watch(page, () => void load(), { immediate: true })
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="cute-card mb-4 flex items-center justify-between gap-3 p-4">
      <div>
        <h1 class="text-base font-bold text-text">📚 我的帖子</h1>
        <p class="mt-0.5 text-xs text-text-muted">共 {{ total }} 篇，按发布时间倒序</p>
      </div>
      <RouterLink
        :to="{ name: 'post-create' }"
        class="cute-btn shrink-0 bg-primary font-semibold text-white hover:shadow-card"
      >
        ✏️ 去发帖
      </RouterLink>
    </div>

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

    <div v-else-if="errorMessage" class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div class="text-5xl">😢</div>
      <p class="text-base font-semibold text-text">呜…加载失败了</p>
      <p class="text-sm text-text-muted">{{ errorMessage }}</p>
      <button type="button" class="cute-btn bg-primary text-white" @click="load">再试一次</button>
    </div>

    <div v-else-if="posts.length === 0" class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div class="text-5xl">🖍️</div>
      <p class="text-base font-semibold text-text">还没有发过帖子哦～</p>
      <p class="text-sm text-text-muted">你的第一篇分享，会从哪开始呢？</p>
      <RouterLink
        :to="{ name: 'post-create' }"
        class="cute-btn mt-1 bg-primary font-semibold text-white hover:shadow-card"
      >
        ✏️ 去发帖
      </RouterLink>
    </div>

    <template v-else>
      <div class="space-y-4">
        <PostCard v-for="post in posts" :key="post.id" :post="post" />
      </div>
      <Pagination :page="page" :total-pages="totalPages" @change="(value: number) => (page = value)" />
    </template>
  </div>
</template>
