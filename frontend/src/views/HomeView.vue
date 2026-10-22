<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { fetchBoards } from '@/api/board'
import { fetchPosts, fetchRecommendedPosts, type PostOrdering } from '@/api/post'
import type { Board, Post } from '@/api/types'
import PostCard from '@/components/post/PostCard.vue'
import { compactCount } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 10

const boards = ref<Board[]>([])
const boardsLoading = ref(true)

const posts = ref<Post[]>([])
const postsLoading = ref(true)
const total = ref(0)
const errorMessage = ref('')

// 站长推荐：与左侧分区筛选无关，始终取全站精华帖
const recommended = ref<Post[]>([])
const recommendedLoading = ref(true)

// 小屏（<lg）下分区导航默认折叠，点「展开」才显示
const navOpen = ref(false)

const activeSlug = computed(() => (route.params.slug as string | undefined) ?? '')
const activeBoard = computed(() => boards.value.find((item) => item.slug === activeSlug.value) ?? null)
const isAll = computed(() => activeSlug.value === '')

const page = computed(() => {
  const value = Number(route.query.page)
  return Number.isFinite(value) && value > 0 ? Math.floor(value) : 1
})
const sortKey = computed(() => (route.query.order === 'hot' ? 'hot' : 'latest'))
const ordering = computed<PostOrdering>(() => (sortKey.value === 'hot' ? '-like_count' : '-created_at'))
const search = computed(() => (route.query.search as string | undefined) ?? '')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const pageNumbers = computed(() => {
  const current = page.value
  const last = totalPages.value
  const start = Math.max(1, current - 2)
  const end = Math.min(last, start + 4)
  const numbers: number[] = []
  for (let i = start; i <= end; i += 1) numbers.push(i)
  return numbers
})

async function loadBoards(): Promise<void> {
  boardsLoading.value = true
  try {
    boards.value = await fetchBoards()
  } catch {
    boards.value = []
  } finally {
    boardsLoading.value = false
  }
}

async function loadPosts(): Promise<void> {
  postsLoading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchPosts({
      board: activeSlug.value || undefined,
      page: page.value,
      page_size: PAGE_SIZE,
      ordering: ordering.value,
      search: search.value || undefined,
    })
    posts.value = data.results
    total.value = data.count
  } catch (error) {
    posts.value = []
    total.value = 0
    errorMessage.value = error instanceof Error ? error.message : '加载失败，请稍后重试'
  } finally {
    postsLoading.value = false
  }
}

/** 以当前筛选条件为底，生成新的 query（page 默认回到第 1 页）。 */
function buildQuery(patch: Record<string, string | number | undefined> = {}): Record<string, string> {
  const merged: Record<string, string | number | undefined> = {
    search: search.value || undefined,
    order: sortKey.value === 'hot' ? 'hot' : undefined,
    ...patch,
  }
  const query: Record<string, string> = {}
  Object.entries(merged).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query[key] = String(value)
  })
  return query
}

function selectBoard(slug: string): void {
  if (slug === activeSlug.value) return
  navOpen.value = false // 小屏选中后自动收起，避免占屏
  if (slug) {
    router.push({ name: 'board', params: { slug }, query: buildQuery() })
  } else {
    router.push({ name: 'home', query: buildQuery() })
  }
}

function switchOrder(order: 'latest' | 'hot'): void {
  if (order === sortKey.value) return
  router.push({ path: route.path, query: buildQuery({ order: order === 'hot' ? 'hot' : undefined }) })
}

function goPage(target: number): void {
  if (target < 1 || target > totalPages.value || target === page.value) return
  router.push({ path: route.path, query: buildQuery({ page: target }) })
}

function onCompose(): void {
  // 未登录时由路由守卫（requiresAuth）拦到登录页，并带上 redirect
  router.push({ name: 'post-create' })
}

async function loadRecommended(): Promise<void> {
  recommendedLoading.value = true
  try {
    recommended.value = await fetchRecommendedPosts()
  } catch {
    recommended.value = []
  } finally {
    recommendedLoading.value = false
  }
}

onMounted(() => {
  loadBoards()
  loadRecommended()
})

watch(
  () => route.fullPath,
  () => {
    loadPosts()
  },
  { immediate: true },
)
</script>

<template>
  <div class="grid grid-cols-1 gap-4 sm:gap-5 lg:grid-cols-[240px_minmax(0,1fr)]">
    <!-- 左侧栏：全局分区导航（桌面固定吸附，移动端折叠） -->
    <aside class="min-w-0 lg:sticky lg:top-20 lg:h-max">
      <nav class="cute-card p-3">
        <div class="flex items-center justify-between gap-2 px-1 pb-2">
          <p class="text-xs font-semibold text-text-muted">分区导航 🐾</p>
          <button
            type="button"
            class="rounded-full px-2 py-1 text-[11px] text-text-muted transition hover:bg-surface-2 hover:text-text lg:hidden"
            :aria-expanded="navOpen"
            @click="navOpen = !navOpen"
          >
            {{ navOpen ? '收起 ▴' : '展开 ▾' }}
          </button>
        </div>

        <!-- 小屏折叠 / 大屏始终展开 -->
        <div :class="navOpen ? 'block' : 'hidden lg:block'">
          <div v-if="boardsLoading" class="space-y-2 px-1 pb-1">
            <div v-for="n in 5" :key="n" class="h-9 animate-pulse rounded-2xl bg-surface-2" />
          </div>

          <ul v-else class="space-y-1">
            <li>
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-2xl px-2.5 py-2 text-left text-sm transition"
                :class="isAll ? 'bg-primary-soft font-semibold text-primary' : 'text-text hover:bg-surface-2'"
                @click="selectBoard('')"
              >
                <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-surface-2 text-base">🏠</span>
                <span class="flex-1 truncate">全部</span>
              </button>
            </li>
            <li v-for="board in boards" :key="board.id">
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-2xl px-2.5 py-2 text-left text-sm transition"
                :class="
                  board.slug === activeSlug
                    ? 'bg-primary-soft font-semibold text-primary'
                    : 'text-text hover:bg-surface-2'
                "
                @click="selectBoard(board.slug)"
              >
                <span
                  class="grid h-8 w-8 shrink-0 place-items-center rounded-xl text-base"
                  :style="{ backgroundColor: board.color + '22', color: board.color }"
                >
                  {{ board.icon }}
                </span>
                <span class="flex-1 truncate">{{ board.name }}</span>
                <span
                  class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] text-text-muted"
                  :style="{ backgroundColor: board.color + '1A' }"
                >
                  {{ compactCount(board.post_count) }}
                </span>
              </button>
            </li>
          </ul>
        </div>
      </nav>
    </aside>

    <!-- 主内容区：顶部站长推荐，下方帖子列表 -->
    <section class="min-w-0 space-y-4 sm:space-y-5">
      <!-- 站长推荐 -->
      <div class="cute-card overflow-hidden">
        <div
          class="flex items-center justify-between gap-2 px-4 py-3"
          :style="{ background: 'var(--gradient-hero)' }"
        >
          <div class="min-w-0">
            <p class="text-sm font-semibold text-text">⭐ 站长推荐</p>
            <p class="mt-0.5 text-[11px] text-text-muted">编辑部精选 · 从精华帖里挑出来的</p>
          </div>
          <span class="shrink-0 text-lg" aria-hidden="true">✨</span>
        </div>

        <div v-if="recommendedLoading" class="grid gap-3 p-3 sm:grid-cols-2 sm:p-4 xl:grid-cols-3">
          <div v-for="n in 3" :key="n" class="h-[74px] animate-pulse rounded-2xl bg-surface-2" />
        </div>

        <div v-else-if="recommended.length" class="grid gap-3 p-3 sm:grid-cols-2 sm:p-4 xl:grid-cols-3">
          <RouterLink
            v-for="item in recommended"
            :key="item.id"
            :to="{ name: 'post-detail', params: { id: item.id } }"
            class="group flex items-center gap-3 rounded-2xl border border-border bg-surface-2 p-3 transition hover:-translate-y-0.5 hover:border-primary hover:bg-primary-soft"
          >
            <span
              class="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-lg"
              :style="{ backgroundColor: item.board.color + '22', color: item.board.color }"
            >
              {{ item.board.icon }}
            </span>
            <span class="min-w-0 flex-1">
              <span class="line-clamp-2 text-sm font-medium leading-snug text-text">{{ item.title }}</span>
              <span class="mt-1 block truncate text-[11px] text-text-muted">
                {{ item.board.name }} · {{ compactCount(item.like_count) }} 赞
              </span>
            </span>
            <span class="shrink-0 text-xs text-text-muted transition group-hover:translate-x-0.5">→</span>
          </RouterLink>
        </div>

        <p v-else class="px-4 py-6 text-center text-xs text-text-muted">站长还没推荐，先去逛逛吧～</p>
      </div>

      <!-- 列表工具条：发帖 + 当前分区 + 排序 -->
      <div class="cute-card flex flex-wrap items-center justify-between gap-3 p-3">
        <div class="flex min-w-0 items-center gap-2">
          <button
            type="button"
            class="cute-btn shrink-0 bg-primary font-semibold text-white hover:shadow-card hover:brightness-105"
            @click="onCompose"
          >
            ✏️ 发帖
          </button>
          <p class="truncate text-sm text-text-muted">
            {{ isAll ? '全部帖子' : activeBoard ? `${activeBoard.icon} ${activeBoard.name}` : '分区' }}
            <span v-if="search" class="ml-1 text-xs">· 搜索「{{ search }}」</span>
          </p>
        </div>

        <div class="flex shrink-0 items-center gap-1 rounded-full bg-surface-2 p-1">
          <button
            type="button"
            class="rounded-full px-3 py-1.5 text-xs font-medium transition"
            :class="sortKey === 'latest' ? 'bg-surface text-primary shadow-card' : 'text-text-muted hover:text-text'"
            @click="switchOrder('latest')"
          >
            最新
          </button>
          <button
            type="button"
            class="rounded-full px-3 py-1.5 text-xs font-medium transition"
            :class="sortKey === 'hot' ? 'bg-surface text-primary shadow-card' : 'text-text-muted hover:text-text'"
            @click="switchOrder('hot')"
          >
            最热
          </button>
        </div>
      </div>

      <!-- 骨架屏 -->
      <div v-if="postsLoading" class="space-y-4">
        <div v-for="n in 3" :key="n" class="cute-card flex gap-4 p-4">
          <div class="h-24 w-24 shrink-0 animate-pulse rounded-2xl bg-surface-2 sm:h-28 sm:w-40" />
          <div class="flex-1 space-y-3 py-1">
            <div class="h-4 w-1/2 animate-pulse rounded-full bg-surface-2" />
            <div class="h-3 w-full animate-pulse rounded-full bg-surface-2" />
            <div class="h-3 w-2/3 animate-pulse rounded-full bg-surface-2" />
            <div class="h-6 w-28 animate-pulse rounded-full bg-surface-2" />
          </div>
        </div>
      </div>

      <!-- 错误态 -->
      <div
        v-else-if="errorMessage"
        class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center"
      >
        <div class="text-5xl">😢</div>
        <p class="text-base font-semibold text-text">呜…帖子加载失败了</p>
        <p class="text-sm text-text-muted">{{ errorMessage }}</p>
        <button type="button" class="cute-btn bg-primary text-white" @click="loadPosts">再试一次</button>
      </div>

      <!-- 空态：可爱插画式，不留白屏 -->
      <div
        v-else-if="posts.length === 0"
        class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center"
      >
        <div class="text-5xl">🎐</div>
        <p class="text-base font-semibold text-text">
          {{ search ? '没有找到相关帖子呢～' : '这个分区还静悄悄的～' }}
        </p>
        <p class="text-sm text-text-muted">
          {{ search ? '换个关键词试试，或者去别的分区逛逛吧！' : '快来发出第一张贴，让这里热闹起来！' }}
        </p>
      </div>

      <!-- 帖子列表 -->
      <div v-else class="space-y-4">
        <PostCard v-for="post in posts" :key="post.id" :post="post" />
      </div>

      <!-- 分页器 -->
      <div v-if="!postsLoading && !errorMessage && total > 0" class="flex items-center justify-center gap-2">
        <button
          type="button"
          class="cute-btn border border-border bg-surface text-text disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="page <= 1"
          @click="goPage(page - 1)"
        >
          上一页
        </button>
        <button
          v-for="n in pageNumbers"
          :key="n"
          type="button"
          class="h-9 w-9 rounded-full text-sm transition"
          :class="n === page ? 'bg-primary font-semibold text-white' : 'bg-surface-2 text-text hover:bg-primary-soft'"
          @click="goPage(n)"
        >
          {{ n }}
        </button>
        <button
          type="button"
          class="cute-btn border border-border bg-surface text-text disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="page >= totalPages"
          @click="goPage(page + 1)"
        >
          下一页
        </button>
      </div>
    </section>
  </div>
</template>
