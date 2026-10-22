<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { fetchFollowers, fetchFriends } from '@/api/social'
import type { UserBrief } from '@/api/types'
import { useUserStore } from '@/stores/user'
import { fromNow } from '@/utils/format'

/** 一位好友 / 粉丝的展示数据，两种模式共用同一套行结构。 */
interface SocialRow {
  id: number
  user: UserBrief
  time: string
}

const PAGE_SIZE = 20

const route = useRoute()
const userStore = useUserStore()

/** 好友与粉丝共用同一个组件，靠路由 meta 区分模式。 */
const mode = computed<'friends' | 'fans'>(() =>
  route.meta.socialMode === 'fans' ? 'fans' : 'friends',
)
const isFriends = computed(() => mode.value === 'friends')

const rows = ref<SocialRow[]>([])
const count = ref(0)
const page = ref(0)
const loading = ref(false)
const loaded = ref(false)
const error = ref('')

const title = computed(() => (isFriends.value ? '🤝 我的好友' : '🌟 我的粉丝'))
const subtitle = computed(() =>
  isFriends.value
    ? '已经互相加为好友的小伙伴，随时可以去 Ta 的主页逛逛～'
    : '正在关注你的小可爱们，也去和 Ta 打个招呼吧～',
)
const emptyTitle = computed(() =>
  isFriends.value ? '还没有好友呢，去和大家交个朋友吧～' : '还没有粉丝，多发点可爱的内容吧～',
)
const timeLabel = computed(() => (isFriends.value ? '好友自' : '关注于'))

async function load(): Promise<void> {
  if (loading.value || !userStore.user) return
  loading.value = true
  error.value = ''
  const nextPage = page.value + 1

  try {
    if (isFriends.value) {
      const data = await fetchFriends({ page: nextPage, page_size: PAGE_SIZE })
      rows.value.push(
        ...data.results.map((item) => ({
          id: item.id,
          user: item.user,
          time: item.friends_since,
        })),
      )
      count.value = data.count
    } else {
      const data = await fetchFollowers(userStore.user.id, {
        page: nextPage,
        page_size: PAGE_SIZE,
      })
      rows.value.push(
        ...data.results.map((item) => ({
          id: item.id,
          user: item.user,
          time: item.followed_at,
        })),
      )
      count.value = data.count
    }
    page.value = nextPage
    loaded.value = true
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function resetAndLoad(): void {
  rows.value = []
  count.value = 0
  page.value = 0
  loaded.value = false
  error.value = ''
  void load()
}

// 好友 -> 粉丝 是同一组件实例，切换路由时要重新拉数据
watch(mode, resetAndLoad, { immediate: true })
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-4">
    <section class="cute-card relative overflow-hidden p-5 sm:p-6">
      <div class="absolute inset-x-0 top-0 h-16 opacity-60" :style="{ background: 'var(--gradient-hero)' }" />
      <span class="pointer-events-none absolute right-5 top-2 animate-floaty text-xl opacity-60" aria-hidden="true">🐾</span>
      <div class="relative">
        <h1 class="text-lg font-bold text-text">{{ title }}</h1>
        <p class="mt-1 text-xs text-text-muted sm:text-sm">{{ subtitle }}</p>
        <p class="mt-2 text-[11px] text-text-muted">
          共 <span class="font-semibold text-primary">{{ count }}</span> 位
        </p>
      </div>
    </section>

    <div v-if="loading && !rows.length" class="space-y-3">
      <div v-for="n in 3" :key="n" class="cute-card h-16 animate-pulse" />
    </div>

    <div v-else-if="error" class="cute-card flex flex-col items-center gap-3 px-6 py-12 text-center">
      <div class="text-5xl">😿</div>
      <p class="text-sm text-text-muted">{{ error }}</p>
      <button type="button" class="cute-btn bg-primary text-white" @click="resetAndLoad">再试一次</button>
    </div>

    <div
      v-else-if="loaded && !rows.length"
      class="cute-card flex flex-col items-center gap-2 px-6 py-14 text-center"
    >
      <div class="text-5xl">🎐</div>
      <p class="text-base font-semibold text-text">{{ emptyTitle }}</p>
      <RouterLink to="/" class="cute-btn mt-1 bg-primary text-white">🏠 回首页逛逛</RouterLink>
    </div>

    <template v-else>
      <div class="space-y-3">
        <RouterLink
          v-for="row in rows"
          :key="row.id"
          :to="{ name: 'user-profile', params: { id: row.user.id } }"
          class="cute-card flex items-center gap-3 p-3 transition hover:-translate-y-0.5 hover:shadow-card"
        >
          <img
            v-if="row.user.avatar"
            :src="row.user.avatar"
            :alt="row.user.display_name"
            class="h-11 w-11 shrink-0 rounded-full object-cover"
          />
          <span
            v-else
            class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-primary-soft text-sm font-bold text-text"
          >
            {{ (row.user.display_name || '喵').slice(0, 1) }}
          </span>

          <span class="min-w-0 flex-1">
            <span class="flex items-center gap-1.5">
              <span class="truncate text-sm font-semibold text-text">{{ row.user.display_name }}</span>
              <span class="shrink-0 rounded-full bg-surface-2 px-1.5 py-0.5 text-[10px] text-text-muted">
                Lv.{{ row.user.level }}
              </span>
            </span>
            <span class="mt-0.5 block truncate text-[11px] text-text-muted">@{{ row.user.username }}</span>
          </span>

          <span class="shrink-0 text-right text-[11px] text-text-muted">
            {{ timeLabel }} {{ fromNow(row.time) }}
          </span>
          <span class="shrink-0 text-text-muted">›</span>
        </RouterLink>
      </div>

      <div v-if="rows.length < count" class="flex justify-center">
        <button
          type="button"
          class="cute-btn border border-border bg-surface text-text hover:shadow-card disabled:opacity-60"
          :disabled="loading"
          @click="load"
        >
          {{ loading ? '加载中…' : '加载更多' }}
        </button>
      </div>
    </template>
  </div>
</template>
