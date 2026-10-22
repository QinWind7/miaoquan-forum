<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/request'
import { sendFriendRequest, toggleFollow } from '@/api/social'
import type { LikedPost, Post, PublicProfile } from '@/api/types'
import { fetchUserLikes, fetchUserPosts, fetchUserProfile, updateMyPrivacy } from '@/api/user'
import PostCard from '@/components/post/PostCard.vue'
import { useUserStore } from '@/stores/user'
import { compactCount } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const PAGE_SIZE = 20

const userId = computed(() => Number(route.params.id))
const isSelf = computed(() => userStore.user?.id === userId.value)

const profile = ref<PublicProfile | null>(null)
const profileLoading = ref(true)
const profileError = ref('')

type TabKey = 'posts' | 'likes'
interface TabState {
  items: (Post | LikedPost)[]
  count: number
  page: number
  loading: boolean
  loaded: boolean
  hidden: boolean
  error: string
}

function emptyTab(): TabState {
  return { items: [], count: 0, page: 0, loading: false, loaded: false, hidden: false, error: '' }
}

const tabs = reactive<Record<TabKey, TabState>>({ posts: emptyTab(), likes: emptyTab() })
const activeTab = ref<TabKey>('posts')

const profileName = computed(() => profile.value?.display_name || profile.value?.username || '喵')
const joinedAt = computed(() => (profile.value?.date_joined ?? '').slice(0, 10))

const postsTabLabel = computed(() => (isSelf.value ? '📚 我的发帖' : '📚 Ta 的发帖'))
const likesTabLabel = computed(() => (isSelf.value ? '💗 我的点赞' : '💗 Ta 的点赞'))
const emptyText = computed(() => {
  if (isSelf.value) {
    return activeTab.value === 'posts' ? '你还没有发过帖子～' : '你还没有点赞过帖子～'
  }
  return activeTab.value === 'posts' ? 'Ta 还没有发过帖子～' : 'Ta 还没有点赞过帖子～'
})

const privacySaving = ref(false)
const privacyError = ref('')

// 社交操作（关注 / 好友申请）共用一套忙碌与错误状态，避免同时点两次
const socialBusy = ref(false)
const socialError = ref('')

function ensureLogin(): boolean {
  if (userStore.isLoggedIn) return true
  router.push({ name: 'login', query: { redirect: route.fullPath } })
  return false
}

async function onToggleFollow(): Promise<void> {
  if (!profile.value || socialBusy.value) return
  if (!ensureLogin()) return
  socialBusy.value = true
  socialError.value = ''
  try {
    const result = await toggleFollow(profile.value.id)
    profile.value.is_following = result.following
    profile.value.follower_count = result.follower_count
  } catch (error) {
    socialError.value = error instanceof Error ? error.message : '操作失败，请稍后重试'
  } finally {
    socialBusy.value = false
  }
}

async function onSendFriendRequest(): Promise<void> {
  if (!profile.value || socialBusy.value) return
  if (!ensureLogin()) return
  socialBusy.value = true
  socialError.value = ''
  try {
    const result = await sendFriendRequest(profile.value.id)
    // 对方此前已申请过我时，后端会自动互相通过（status = 1）
    profile.value.is_friend = result.status === 1
    profile.value.has_pending_request = result.status === 0
  } catch (error) {
    socialError.value = error instanceof Error ? error.message : '申请发送失败，请稍后重试'
  } finally {
    socialBusy.value = false
  }
}

/** 已是好友 → 直接跳到私聊页并打开与该用户的会话。 */
function onChat(): void {
  if (!profile.value) return
  router.push({ name: 'chat', query: { user: String(profile.value.id) } })
}

async function loadProfile(): Promise<void> {
  profileLoading.value = true
  profileError.value = ''
  profile.value = null
  try {
    profile.value = await fetchUserProfile(userId.value)
  } catch (error) {
    profileError.value =
      error instanceof ApiError && error.status === 404
        ? '这个用户不存在或已注销～'
        : error instanceof Error
          ? error.message
          : '资料加载失败'
  } finally {
    profileLoading.value = false
  }
}

async function loadTab(key: TabKey, reset = false): Promise<void> {
  const state = tabs[key]
  if (state.loading) return
  if (!reset && state.loaded) return

  if (reset) {
    state.items = []
    state.count = 0
    state.page = 0
    state.loaded = false
  }

  state.loading = true
  state.error = ''
  state.hidden = false
  const nextPage = state.page + 1

  try {
    const data =
      key === 'posts'
        ? await fetchUserPosts(userId.value, { page: nextPage, page_size: PAGE_SIZE })
        : await fetchUserLikes(userId.value, { page: nextPage, page_size: PAGE_SIZE })
    state.items = reset ? data.results : [...state.items, ...data.results]
    state.count = data.count
    state.page = nextPage
    state.loaded = true
  } catch (error) {
    if (error instanceof ApiError && error.status === 403) {
      // 对方开启了隐私开关：展示可爱提示，而不是错误弹窗
      state.hidden = true
      state.items = []
      state.count = 0
      state.loaded = true
    } else {
      state.error = error instanceof Error ? error.message : '加载失败，请稍后重试'
    }
  } finally {
    state.loading = false
  }
}

function switchTab(key: TabKey): void {
  if (activeTab.value === key) return
  activeTab.value = key
  void loadTab(key)
}

async function onPrivacyChange(field: 'hide_posts' | 'hide_likes', value: boolean): Promise<void> {
  if (!profile.value || privacySaving.value) return
  privacySaving.value = true
  privacyError.value = ''
  try {
    const updated = await updateMyPrivacy({ [field]: value })
    userStore.setUser(updated)
    profile.value.hide_posts = updated.hide_posts
    profile.value.hide_likes = updated.hide_likes
  } catch (error) {
    // 回滚 UI 到服务端的真实状态
    profile.value[field] = !value
    privacyError.value = error instanceof Error ? error.message : '保存失败，请稍后重试'
  } finally {
    privacySaving.value = false
  }
}

watch(
  userId,
  () => {
    tabs.posts = emptyTab()
    tabs.likes = emptyTab()
    activeTab.value = 'posts'
    privacyError.value = ''
    socialError.value = ''
    void loadProfile()
    // 两个 Tab 都预取一次：资料卡上的「发帖 / 点赞」统计才准确
    void loadTab('posts')
    void loadTab('likes')
  },
  { immediate: true },
)
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-4">
    <!-- 资料卡 -->
    <div v-if="profileLoading" class="cute-card h-40 animate-pulse" />

    <div v-else-if="profileError || !profile" class="cute-card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div class="text-5xl">😿</div>
      <p class="text-base font-semibold text-text">呜…找不到这位小伙伴</p>
      <p class="text-sm text-text-muted">{{ profileError || 'Ta 可能已经注销啦～' }}</p>
      <button type="button" class="cute-btn bg-primary text-white" @click="loadProfile">再试一次</button>
    </div>

    <template v-else>
      <section class="cute-card relative overflow-hidden p-5 sm:p-6">
        <div class="absolute inset-x-0 top-0 h-20 opacity-70" :style="{ background: 'var(--gradient-hero)' }" />
        <span class="pointer-events-none absolute right-5 top-3 animate-floaty text-2xl opacity-60" aria-hidden="true">🐾</span>

        <div class="relative flex flex-col items-center gap-4 sm:flex-row sm:items-end">
          <div class="relative shrink-0">
            <img
              v-if="profile.avatar"
              :src="profile.avatar"
              :alt="profileName"
              class="h-20 w-20 rounded-full border-4 border-surface object-cover shadow-card"
            />
            <span
              v-else
              class="grid h-20 w-20 place-items-center rounded-full border-4 border-surface bg-primary-soft text-2xl font-bold text-text shadow-card"
            >
              {{ profileName.slice(0, 1) }}
            </span>

            <!-- 他人主页：头像右上角关注按钮 -->
            <button
              v-if="!isSelf"
              type="button"
              class="absolute -right-2 -top-2 rounded-full px-2.5 py-1 text-[11px] font-semibold shadow-card transition disabled:opacity-60"
              :class="
                profile.is_following
                  ? 'border border-border bg-surface text-text-muted hover:text-text'
                  : 'bg-primary text-white hover:-translate-y-0.5'
              "
              :disabled="socialBusy"
              @click="onToggleFollow"
            >
              {{ profile.is_following ? '已关注' : '＋ 关注' }}
            </button>
          </div>

          <div class="min-w-0 flex-1 text-center sm:text-left">
            <div class="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
              <h1 class="truncate text-xl font-bold text-text">{{ profileName }}</h1>
              <span class="rounded-full bg-surface-2 px-2 py-0.5 text-[11px] text-text-muted">
                Lv.{{ profile.level }}
              </span>
              <span
                v-if="profile.is_staff"
                class="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-semibold text-text"
              >
                管理员
              </span>
              <span v-if="isSelf" class="rounded-full bg-primary-soft px-2 py-0.5 text-[11px] font-semibold text-primary">
                这是你呀
              </span>
            </div>
            <p class="mt-1 text-xs text-text-muted">@{{ profile.username }} · 加入于 {{ joinedAt }}</p>

            <!-- 他人主页：昵称下方的加好友 / 私聊入口 -->
            <div
              v-if="!isSelf"
              class="mt-2 flex flex-wrap items-center justify-center gap-2 sm:justify-start"
            >
              <button
                v-if="profile.is_friend"
                type="button"
                class="cute-btn bg-primary px-3 py-1.5 text-xs text-white hover:shadow-card"
                @click="onChat"
              >
                💬 发私聊
              </button>
              <button
                v-else-if="profile.has_pending_request"
                type="button"
                class="cute-btn cursor-default border border-border bg-surface-2 px-3 py-1.5 text-xs text-text-muted"
                disabled
              >
                ⏳ 已发送申请
              </button>
              <button
                v-else
                type="button"
                class="cute-btn border border-border bg-surface-2 px-3 py-1.5 text-xs text-text hover:shadow-card disabled:opacity-60"
                :disabled="socialBusy"
                @click="onSendFriendRequest"
              >
                🐾 添加好友
              </button>
            </div>
            <p v-if="socialError" class="mt-1 text-xs text-primary">😿 {{ socialError }}</p>

            <p class="mt-2 line-clamp-2 text-sm text-text">
              {{ profile.bio || '这位小可爱还没有写简介～' }}
            </p>
          </div>

          <div class="flex shrink-0 gap-4 text-center">
            <div>
              <p class="text-base font-bold text-text">{{ compactCount(tabs.posts.count) }}</p>
              <p class="text-[11px] text-text-muted">发帖</p>
            </div>
            <div>
              <p class="text-base font-bold text-text">{{ compactCount(tabs.likes.count) }}</p>
              <p class="text-[11px] text-text-muted">点赞</p>
            </div>
            <div>
              <p class="text-base font-bold text-text">{{ compactCount(profile.follower_count) }}</p>
              <p class="text-[11px] text-text-muted">粉丝</p>
            </div>
            <div>
              <p class="text-base font-bold text-text">{{ compactCount(profile.points) }}</p>
              <p class="text-[11px] text-text-muted">积分</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 自己的主页：隐私设置 -->
      <section v-if="isSelf" class="cute-card p-4 sm:p-5">
        <div class="mb-3 flex items-center justify-between gap-2">
          <div>
            <p class="text-sm font-semibold text-text">🔒 隐私设置</p>
            <p class="mt-0.5 text-[11px] text-text-muted">
              隐藏后，别人打开你的主页只会看到一句可爱提示；你自己仍能正常查看。
            </p>
          </div>
          <span v-if="privacySaving" class="shrink-0 text-[11px] text-text-muted">保存中…</span>
        </div>

        <div class="grid gap-2 sm:grid-cols-2">
          <label class="flex cursor-pointer items-center gap-3 rounded-2xl bg-surface-2 px-3 py-2.5">
            <input
              type="checkbox"
              class="sr-only"
              :checked="profile.hide_posts"
              :disabled="privacySaving"
              @change="onPrivacyChange('hide_posts', ($event.target as HTMLInputElement).checked)"
            />
            <span
              class="relative h-6 w-11 shrink-0 rounded-full transition"
              :class="profile.hide_posts ? 'bg-primary' : 'bg-border'"
            >
              <span
                class="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition"
                :class="profile.hide_posts ? 'translate-x-5' : ''"
              />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block text-sm text-text">隐藏我的发帖</span>
              <span class="block text-[11px] text-text-muted">
                {{ profile.hide_posts ? '已隐藏，别人看不到你发的帖' : '当前公开' }}
              </span>
            </span>
          </label>

          <label class="flex cursor-pointer items-center gap-3 rounded-2xl bg-surface-2 px-3 py-2.5">
            <input
              type="checkbox"
              class="sr-only"
              :checked="profile.hide_likes"
              :disabled="privacySaving"
              @change="onPrivacyChange('hide_likes', ($event.target as HTMLInputElement).checked)"
            />
            <span
              class="relative h-6 w-11 shrink-0 rounded-full transition"
              :class="profile.hide_likes ? 'bg-primary' : 'bg-border'"
            >
              <span
                class="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition"
                :class="profile.hide_likes ? 'translate-x-5' : ''"
              />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block text-sm text-text">隐藏我的点赞</span>
              <span class="block text-[11px] text-text-muted">
                {{ profile.hide_likes ? '已隐藏，别人看不到你赞过的帖' : '当前公开' }}
              </span>
            </span>
          </label>
        </div>

        <p v-if="privacyError" class="mt-2 text-xs text-primary">😿 {{ privacyError }}</p>
      </section>

      <!-- Tab 切换 -->
      <div class="cute-card flex items-center gap-1 p-1.5">
        <button
          type="button"
          class="flex-1 rounded-2xl px-3 py-2 text-sm font-medium transition"
          :class="activeTab === 'posts' ? 'bg-primary-soft text-primary' : 'text-text-muted hover:bg-surface-2 hover:text-text'"
          @click="switchTab('posts')"
        >
          {{ postsTabLabel }}
          <span class="ml-1 text-[11px]">{{ tabs.posts.loaded && !tabs.posts.hidden ? tabs.posts.count : '' }}</span>
        </button>
        <button
          type="button"
          class="flex-1 rounded-2xl px-3 py-2 text-sm font-medium transition"
          :class="activeTab === 'likes' ? 'bg-primary-soft text-primary' : 'text-text-muted hover:bg-surface-2 hover:text-text'"
          @click="switchTab('likes')"
        >
          {{ likesTabLabel }}
          <span class="ml-1 text-[11px]">{{ tabs.likes.loaded && !tabs.likes.hidden ? tabs.likes.count : '' }}</span>
        </button>
      </div>

      <!-- 列表内容 -->
      <template v-if="tabs[activeTab].hidden">
        <div class="cute-card flex flex-col items-center gap-2 px-6 py-14 text-center">
          <div class="text-5xl">🙈</div>
          <p class="text-base font-semibold text-text">这位小可爱把动态藏起来啦~ 🐾</p>
          <p class="text-sm text-text-muted">可能想保留一点自己的小秘密，去别处逛逛吧～</p>
        </div>
      </template>

      <template v-else-if="tabs[activeTab].loading && !tabs[activeTab].items.length">
        <div class="space-y-4">
          <div v-for="n in 2" :key="n" class="cute-card h-32 animate-pulse" />
        </div>
      </template>

      <template v-else-if="tabs[activeTab].error">
        <div class="cute-card flex flex-col items-center gap-3 px-6 py-12 text-center">
          <div class="text-5xl">😢</div>
          <p class="text-sm text-text-muted">{{ tabs[activeTab].error }}</p>
          <button type="button" class="cute-btn bg-primary text-white" @click="loadTab(activeTab, true)">
            再试一次
          </button>
        </div>
      </template>

      <template v-else-if="!tabs[activeTab].items.length">
        <div class="cute-card flex flex-col items-center gap-2 px-6 py-14 text-center">
          <div class="text-5xl">🎐</div>
          <p class="text-base font-semibold text-text">{{ emptyText }}</p>
          <p class="text-sm text-text-muted">
            {{ isSelf ? '去看看首页，找点感兴趣的内容吧！' : '空空如也，等 Ta 下次来更新～' }}
          </p>
          <button
            v-if="isSelf"
            type="button"
            class="cute-btn mt-1 bg-primary text-white"
            @click="router.push({ name: 'home' })"
          >
            🏠 回首页逛逛
          </button>
        </div>
      </template>

      <template v-else>
        <div class="space-y-4">
          <PostCard v-for="item in tabs[activeTab].items" :key="item.id" :post="item" />
        </div>

        <div
          v-if="tabs[activeTab].items.length < tabs[activeTab].count"
          class="flex justify-center"
        >
          <button
            type="button"
            class="cute-btn border border-border bg-surface text-text hover:shadow-card disabled:opacity-60"
            :disabled="tabs[activeTab].loading"
            @click="loadTab(activeTab)"
          >
            {{ tabs[activeTab].loading ? '加载中…' : '加载更多' }}
          </button>
        </div>
      </template>
    </template>
  </div>
</template>
