<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { deletePost, fetchPost } from '@/api/post'
import type { PostDetail } from '@/api/types'
import CommentList from '@/components/comment/CommentList.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import PostLikeButton from '@/components/post/PostLikeButton.vue'
import { useUserStore } from '@/stores/user'
import { compactCount, fromNow } from '@/utils/format'
import { renderMarkdown } from '@/utils/markdown'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const post = ref<PostDetail | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const confirmOpen = ref(false)
const deleting = ref(false)
const previewUrl = ref<string | null>(null)

const postId = computed(() => Number(route.params.id))
const isAuthor = computed(() => Boolean(post.value && userStore.user?.id === post.value.author.id))
const canManage = computed(() => Boolean(post.value && (isAuthor.value || userStore.user?.is_staff)))
const bodyHtml = computed(() => (post.value ? renderMarkdown(post.value.content) : ''))

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  post.value = null
  try {
    // 详情 GET 会累加浏览数，因此只在进入 / 切换帖子时请求一次，不做轮询
    post.value = await fetchPost(postId.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '帖子加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

/** 评论增删后同步帖子上的评论数。 */
function onCommentsChanged(delta: number): void {
  if (!post.value) return
  post.value.comment_count = Math.max(0, post.value.comment_count + delta)
}

async function onDelete(): Promise<void> {
  if (!post.value || deleting.value) return
  deleting.value = true
  try {
    await deletePost(post.value.id)
    confirmOpen.value = false
    router.push({ name: 'home' })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除失败，请稍后重试'
    confirmOpen.value = false
  } finally {
    deleting.value = false
  }
}

watch(postId, () => void load(), { immediate: true })

/** 返回上一页；没有可回退的历史（如直接打开链接）时退回首页兜底。 */
function goBack(): void {
  if (window.history.state && window.history.state.back) {
    router.back()
  } else {
    router.push({ name: 'home' })
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <!-- 返回上一页：回到帖子列表 / 上一个浏览过的页面 -->
    <button
      type="button"
      class="cute-btn mb-3 border border-border bg-surface-2 text-text hover:shadow-card"
      @click="goBack"
    >
      ← 返回上一页
    </button>

    <!-- 加载骨架 -->
    <div v-if="loading" class="cute-card space-y-4 p-6">
      <div class="h-6 w-2/3 animate-pulse rounded-full bg-surface-2" />
      <div class="h-4 w-1/3 animate-pulse rounded-full bg-surface-2" />
      <div class="h-40 w-full animate-pulse rounded-2xl bg-surface-2" />
      <div class="space-y-2">
        <div class="h-3 w-full animate-pulse rounded-full bg-surface-2" />
        <div class="h-3 w-5/6 animate-pulse rounded-full bg-surface-2" />
        <div class="h-3 w-4/6 animate-pulse rounded-full bg-surface-2" />
      </div>
    </div>

    <!-- 错误态 -->
    <div v-else-if="errorMessage || !post" class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div class="text-5xl">😢</div>
      <p class="text-base font-semibold text-text">呜…这个帖子找不到了</p>
      <p class="text-sm text-text-muted">{{ errorMessage || '它可能已经被删除或正在休息～' }}</p>
      <div class="mt-1 flex gap-3">
        <button type="button" class="cute-btn border border-border bg-surface text-text" @click="load">
          再试一次
        </button>
        <RouterLink :to="{ name: 'home' }" class="cute-btn bg-primary font-semibold text-white">
          🏠 回首页
        </RouterLink>
      </div>
    </div>

    <template v-else>
      <article class="cute-card p-5 sm:p-6">
        <!-- 标记 + 分区徽标 -->
        <div class="mb-3 flex flex-wrap items-center gap-1.5">
          <span
            v-if="post.is_pinned"
            class="rounded-full bg-accent px-2 py-0.5 text-[11px] font-semibold text-text"
          >
            📌 置顶
          </span>
          <span
            v-if="post.is_essence"
            class="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-semibold text-text"
          >
            ✨ 精华
          </span>
          <RouterLink
            :to="{ name: 'board', params: { slug: post.board.slug } }"
            class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
            :style="{ color: post.board.color, backgroundColor: post.board.color + '22' }"
          >
            {{ post.board.icon }} {{ post.board.name }}
          </RouterLink>
        </div>

        <h1 class="text-xl font-bold leading-snug text-text sm:text-2xl">{{ post.title }}</h1>

        <!-- 作者信息 -->
        <div class="mt-3 flex items-center gap-2.5 border-b border-border pb-4">
          <RouterLink
            :to="{ name: 'user-profile', params: { id: post.author.id } }"
            class="shrink-0"
            :title="`查看 ${post.author.display_name} 的主页`"
          >
            <img
              v-if="post.author.avatar"
              :src="post.author.avatar"
              :alt="post.author.display_name"
              class="h-10 w-10 rounded-full object-cover transition hover:opacity-85"
            />
            <span
              v-else
              class="grid h-10 w-10 place-items-center rounded-full bg-primary-soft text-sm font-bold text-text transition hover:opacity-85"
            >
              {{ (post.author.display_name || '喵').slice(0, 1) }}
            </span>
          </RouterLink>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold text-text">
              <RouterLink
                :to="{ name: 'user-profile', params: { id: post.author.id } }"
                class="transition hover:text-primary hover:underline"
              >
                {{ post.author.display_name }}
              </RouterLink>
              <span class="ml-1 rounded-full bg-surface-2 px-1.5 py-0.5 text-[10px] text-text-muted">
                Lv.{{ post.author.level }}
              </span>
            </p>
            <p class="text-xs text-text-muted">{{ fromNow(post.created_at) }}</p>
          </div>
          <span class="shrink-0 text-xs text-text-muted">👀 {{ compactCount(post.view_count) }}</span>
        </div>

        <!-- 图集：九宫格缩略图，点击放大 -->
        <div
          v-if="post.images && post.images.length"
          class="mt-4 grid grid-cols-3 gap-2 sm:max-w-md"
        >
          <button
            v-for="(image, index) in post.images"
            :key="image.url + index"
            type="button"
            class="overflow-hidden rounded-2xl border border-border transition hover:-translate-y-0.5 hover:shadow-card"
            @click="previewUrl = image.url"
          >
            <img :src="image.url" alt="帖子配图" class="aspect-square w-full object-cover" loading="lazy" />
          </button>
        </div>

        <!-- 正文：markdown-it 渲染 + DOMPurify 消毒 -->
        <div class="markdown-body mt-5" v-html="bodyHtml" />

        <!-- 底部操作 -->
        <div class="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
          <div class="flex items-center gap-3 text-xs text-text-muted">
            <PostLikeButton :post="post" />
            <span class="flex items-center gap-1">💬 {{ compactCount(post.comment_count) }}</span>
          </div>

          <div v-if="canManage" class="flex items-center gap-2">
            <RouterLink
              :to="{ name: 'post-edit', params: { id: post.id } }"
              class="cute-btn border border-border bg-surface-2 text-text hover:shadow-card"
            >
              ✏️ 编辑
            </RouterLink>
            <button
              type="button"
              class="cute-btn border border-border bg-surface-2 text-text hover:shadow-card"
              @click="confirmOpen = true"
            >
              🗑️ 删除
            </button>
          </div>
        </div>
      </article>

      <CommentList :post-id="post.id" @changed="onCommentsChanged" />
    </template>

    <!-- 图片放大预览 -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0"
    >
      <div
        v-if="previewUrl"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click="previewUrl = null"
      >
        <div
          class="absolute inset-0 backdrop-blur-sm"
          :style="{ backgroundColor: 'var(--color-text)', opacity: 0.55 }"
        />
        <div class="relative z-10 max-h-full max-w-3xl">
          <img :src="previewUrl" alt="预览" class="max-h-[80vh] w-auto rounded-2xl object-contain" />
          <button
            type="button"
            class="absolute -right-3 -top-3 grid h-9 w-9 place-items-center rounded-full border border-border bg-surface text-sm text-text shadow-card"
            @click.stop="previewUrl = null"
          >
            ✕
          </button>
        </div>
      </div>
    </Transition>

    <ConfirmDialog
      :open="confirmOpen"
      title="真的要删掉这个帖子吗？"
      message="删除后帖子会从列表里消失，不能恢复哦～"
      confirm-text="删除"
      :loading="deleting"
      @confirm="onDelete"
      @cancel="confirmOpen = false"
    />
  </div>
</template>

<style scoped>
.markdown-body {
  word-break: break-word;
}

.markdown-body :deep(p) {
  margin: 0.5rem 0;
  line-height: 1.85;
  color: var(--color-text);
}

.markdown-body :deep(img) {
  max-width: 100%;
  margin: 0.5rem 0;
  border-radius: 12px;
}

.markdown-body :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 0.9rem 0 0.35rem;
  font-weight: 700;
  line-height: 1.4;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.4rem;
  list-style: disc;
}

.markdown-body :deep(code) {
  padding: 0.1rem 0.35rem;
  border-radius: 6px;
  background-color: var(--color-surface-2);
  font-size: 0.85em;
}

.markdown-body :deep(pre) {
  margin: 0.6rem 0;
  padding: 0.75rem;
  border-radius: 12px;
  background-color: var(--color-surface-2);
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background-color: transparent;
}

.markdown-body :deep(blockquote) {
  margin: 0.6rem 0;
  padding-left: 0.8rem;
  border-left: 3px solid var(--color-border);
  color: var(--color-text-muted);
}
</style>
