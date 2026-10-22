<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchComments } from '@/api/comment'
import type { Comment } from '@/api/types'
import CommentEditor from '@/components/comment/CommentEditor.vue'
import CommentItem from '@/components/comment/CommentItem.vue'
import { useUserStore } from '@/stores/user'

const PAGE_SIZE = 10

const props = defineProps<{ postId: number }>()

/** 评论增删后向前抛出增量，供详情页同步帖子上的评论数。 */
const emit = defineEmits<{ (e: 'changed', delta: number): void }>()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const comments = ref<Comment[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const errorMessage = ref('')
const total = ref(0)
const page = ref(1)

const hasMore = computed(() => comments.value.length < total.value)

async function load(reset = false): Promise<void> {
  if (reset) {
    page.value = 1
    loading.value = true
  } else {
    loadingMore.value = true
  }
  errorMessage.value = ''
  try {
    const data = await fetchComments(props.postId, { page: page.value, page_size: PAGE_SIZE })
    comments.value = reset ? data.results : [...comments.value, ...data.results]
    total.value = data.count
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '评论加载失败，请稍后重试'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore(): void {
  if (loadingMore.value || !hasMore.value) return
  page.value += 1
  void load()
}

/** 后端评论列表按 created_at 升序返回，新评论插到列表尾部。 */
function onSubmitted(comment: Comment): void {
  comments.value.push(comment)
  total.value += 1
  emit('changed', 1)
}

function goLogin(): void {
  router.push({ path: '/login', query: { redirect: route.fullPath } })
}

watch(() => props.postId, () => void load(true), { immediate: true })
</script>

<template>
  <section class="cute-card mt-5 p-5">
    <div class="mb-4 flex items-center justify-between gap-2">
      <h2 class="text-base font-bold text-text">💬 评论</h2>
      <span class="text-xs text-text-muted">共 {{ total }} 条</span>
    </div>

    <!-- 顶部评论框 -->
    <div v-if="userStore.isLoggedIn" class="mb-5 rounded-2xl bg-surface-2 p-3">
      <CommentEditor :post-id="postId" @submitted="onSubmitted" />
    </div>
    <div
      v-else
      class="mb-5 flex flex-wrap items-center justify-between gap-2 rounded-2xl bg-surface-2 px-4 py-3"
    >
      <span class="text-sm text-text-muted">登录后就能一起聊天啦～</span>
      <button
        type="button"
        class="cute-btn bg-primary font-semibold text-white hover:shadow-card"
        @click="goLogin"
      >
        去登录
      </button>
    </div>

    <!-- 骨架屏 -->
    <div v-if="loading" class="space-y-4">
      <div v-for="n in 3" :key="n" class="flex gap-3">
        <div class="h-9 w-9 shrink-0 animate-pulse rounded-full bg-surface-2" />
        <div class="flex-1 space-y-2">
          <div class="h-3 w-24 animate-pulse rounded-full bg-surface-2" />
          <div class="h-3 w-2/3 animate-pulse rounded-full bg-surface-2" />
        </div>
      </div>
    </div>

    <!-- 错误态 -->
    <div v-else-if="errorMessage" class="flex flex-col items-center gap-3 py-10 text-center">
      <div class="text-4xl">😢</div>
      <p class="text-sm text-text-muted">{{ errorMessage }}</p>
      <button
        type="button"
        class="cute-btn border border-border bg-surface text-text hover:shadow-card"
        @click="load(true)"
      >
        再试一次
      </button>
    </div>

    <!-- 空态 -->
    <div v-else-if="comments.length === 0" class="flex flex-col items-center gap-2 py-10 text-center">
      <div class="text-4xl">🍥</div>
      <p class="text-sm font-semibold text-text">还没有人评论呢～</p>
      <p class="text-xs text-text-muted">来抢个沙发，说点什么吧！</p>
    </div>

    <!-- 评论列表 -->
    <div v-else class="divide-y divide-border">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        class="py-4 first:pt-0 last:pb-0"
        :comment="comment"
        :post-id="postId"
        @changed="(delta: number) => emit('changed', delta)"
      />
    </div>

    <!-- 加载更多 -->
    <div v-if="!loading && !errorMessage && hasMore" class="mt-5 text-center">
      <button
        type="button"
        class="cute-btn border border-border bg-surface text-text hover:shadow-card disabled:opacity-60"
        :disabled="loadingMore"
        @click="loadMore"
      >
        {{ loadingMore ? '加载中…' : '加载更多评论' }}
      </button>
    </div>
  </section>
</template>
