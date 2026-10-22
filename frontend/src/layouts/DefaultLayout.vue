<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import NotificationBell from '@/components/notification/NotificationBell.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { useClickOutside } from '@/composables/useClickOutside'
import { useTheme } from '@/composables/useTheme'
import { useUnreadStore } from '@/stores/unread'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const unreadStore = useUnreadStore()
const { cloudNotice } = useTheme()

const keyword = ref('')
const menuOpen = ref(false)
const menuRef = ref<HTMLElement | null>(null)
// 手机端搜索框默认收起，点放大镜后再展开
const mobileSearchOpen = ref(false)
const mobileSearchInput = ref<HTMLInputElement | null>(null)

const avatarText = computed(() => (userStore.displayName || '喵').slice(0, 1))

useClickOutside(menuRef, () => {
  menuOpen.value = false
})

async function toggleMobileSearch(): Promise<void> {
  mobileSearchOpen.value = !mobileSearchOpen.value
  if (mobileSearchOpen.value) {
    await nextTick()
    mobileSearchInput.value?.focus()
  }
}

function onAvatarClick(): void {
  mobileSearchOpen.value = false
  menuOpen.value = !menuOpen.value
}

function onSearch(): void {
  const value = keyword.value.trim()
  mobileSearchOpen.value = false
  router.push({ name: 'home', query: value ? { search: value } : {} })
}

/** 顶部「返回主界面」：无论当前在哪一页都回到首页。 */
function goHome(): void {
  router.push({ name: 'home' })
}

async function onLogout(): Promise<void> {
  menuOpen.value = false
  await userStore.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="relative min-h-screen bg-bg">
    <!-- 全局猫咪脚印装饰：纯 CSS/图标，不参与交互 -->
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <span class="absolute left-[5%] top-[16%] animate-floaty text-2xl opacity-25">🐾</span>
      <span
        class="absolute right-[7%] top-[28%] animate-floaty text-xl opacity-20"
        style="animation-delay: -2s"
        >🐾</span
      >
      <span
        class="absolute bottom-[18%] left-[10%] animate-floaty text-xl opacity-20"
        style="animation-delay: -4s"
        >🐾</span
      >
      <span
        class="absolute bottom-[26%] right-[12%] animate-floaty text-2xl opacity-25"
        style="animation-delay: -1s"
        >🐾</span
      >
    </div>

    <header class="sticky top-0 z-40 border-b border-border bg-surface backdrop-blur">
      <div class="mx-auto max-w-7xl px-4">
        <div class="topbar-row flex h-14 items-center gap-2 sm:h-16">
          <RouterLink to="/" class="topbar-logo flex shrink-0 items-center gap-1" aria-label="喵圈首页">
            <span class="text-xl leading-none">🐾</span>
            <span class="topbar-logo-text cat-ears text-base font-bold text-primary sm:text-lg">喵圈</span>
          </RouterLink>

          <!-- 全局搜索：≥md 时与 Logo 同一行；手机端收起为放大镜按钮 -->
          <form class="hidden min-w-0 flex-1 md:block" @submit.prevent="onSearch">
            <div class="relative">
              <span class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted">
                🔍
              </span>
              <input
                v-model="keyword"
                type="search"
                placeholder="搜索帖子 / 关键词…"
                class="cute-input py-2 pl-10 pr-4"
              />
            </div>
          </form>

        <button
          type="button"
          class="topbar-icon grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-surface-2 text-base text-text transition hover:shadow-card md:hidden"
          title="搜索"
          :aria-expanded="mobileSearchOpen"
          @click="toggleMobileSearch"
        >
          🔍
        </button>

        <button
          type="button"
          class="topbar-icon cute-btn shrink-0 border border-border bg-surface-2 px-3 text-text hover:shadow-card sm:px-4"
          title="返回主界面"
          @click="goHome"
        >
          🏠 <span class="topbar-home-text hidden sm:inline">返回主界面</span>
        </button>

        <ThemeSwitcher />

        <template v-if="userStore.isLoggedIn">
          <!-- 手动刷新：方便手机端随时拉取最新未读数 -->
          <button
            type="button"
            class="topbar-icon grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-surface-2 text-sm text-text transition hover:shadow-card"
            title="刷新消息"
            @click="unreadStore.refresh()"
          >
            <span
              class="inline-block transition-transform"
              :class="{ 'animate-spin': unreadStore.refreshing }"
              aria-hidden="true"
            >
              🔄
            </span>
          </button>

          <NotificationBell />

          <div ref="menuRef" class="relative">
            <button
              type="button"
              class="avatar-trigger flex items-center gap-2 rounded-full border border-border bg-surface-2 px-2 py-1.5 transition hover:shadow-card"
              @click="onAvatarClick"
            >
              <img
                v-if="userStore.avatar"
                :src="userStore.avatar"
                :alt="userStore.displayName"
                class="h-7 w-7 rounded-full object-cover"
              />
              <span
                v-else
                class="avatar-fallback grid h-7 w-7 place-items-center rounded-full bg-primary-soft text-xs font-bold text-text"
              >
                {{ avatarText }}
              </span>
              <span class="avatar-name hidden max-w-[8rem] truncate text-sm text-text sm:inline">
                {{ userStore.displayName }}
              </span>
              <span class="avatar-caret text-xs text-text-muted">▾</span>
            </button>

            <Transition
              enter-active-class="transition duration-150 ease-out"
              enter-from-class="opacity-0 -translate-y-1"
              leave-active-class="transition duration-100 ease-in"
              leave-to-class="opacity-0 -translate-y-1"
            >
              <div
                v-if="menuOpen"
                class="topbar-menu absolute right-0 mt-2 w-44 overflow-hidden rounded-2xl border border-border bg-surface p-1.5 shadow-card"
              >
                <div class="px-3 py-2">
                  <p class="truncate text-sm font-semibold text-text">{{ userStore.displayName }}</p>
                  <p class="text-xs text-text-muted">Lv.{{ userStore.user?.level ?? 1 }}</p>
                </div>
                <RouterLink
                  v-if="userStore.user"
                  :to="{ name: 'user-profile', params: { id: userStore.user.id } }"
                  class="block w-full rounded-xl px-3 py-2 text-left text-sm text-text transition hover:bg-primary-soft"
                  @click="menuOpen = false"
                >
                  🐾 我的主页
                </RouterLink>
                <RouterLink
                  :to="{ name: 'chat' }"
                  class="block w-full rounded-xl px-3 py-2 text-left text-sm text-text transition hover:bg-primary-soft"
                  @click="menuOpen = false"
                >
                  💬 我的私聊
                </RouterLink>
                <RouterLink
                  :to="{ name: 'my-friends' }"
                  class="block w-full rounded-xl px-3 py-2 text-left text-sm text-text transition hover:bg-primary-soft"
                  @click="menuOpen = false"
                >
                  🤝 我的好友
                </RouterLink>
                <RouterLink
                  :to="{ name: 'my-fans' }"
                  class="block w-full rounded-xl px-3 py-2 text-left text-sm text-text transition hover:bg-primary-soft"
                  @click="menuOpen = false"
                >
                  🌟 我的粉丝
                </RouterLink>
                <button
                  type="button"
                  class="w-full rounded-xl px-3 py-2 text-left text-sm text-text transition hover:bg-primary-soft"
                  @click="onLogout"
                >
                  退出登录
                </button>
              </div>
            </Transition>
          </div>
        </template>
        <template v-else>
          <div class="flex shrink-0 items-center gap-2">
            <RouterLink
              to="/login"
              class="cute-btn border border-border bg-surface-2 text-text hover:shadow-card"
            >
              登录
            </RouterLink>
            <RouterLink to="/register" class="cute-btn bg-primary text-white hover:shadow-card">
              注册
            </RouterLink>
          </div>
        </template>
        </div>

        <!-- 手机端：点放大镜后在顶栏下方展开搜索框 -->
        <form v-if="mobileSearchOpen" class="pb-2 md:hidden" @submit.prevent="onSearch">
          <div class="relative">
            <span class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted">🔍</span>
            <input
              ref="mobileSearchInput"
              v-model="keyword"
              type="search"
              placeholder="搜索帖子 / 关键词…"
              class="cute-input py-2 pl-10 pr-4"
            />
          </div>
        </form>
      </div>
    </header>

    <!-- 全局欢迎横幅：站外入口 + 站内公告都收进这里，避免挤占导航栏 -->
    <section class="mx-auto max-w-7xl px-4 pt-4">
      <div class="relative overflow-hidden rounded-card border border-border shadow-card">
        <div class="absolute inset-0" :style="{ background: 'var(--gradient-hero)' }" aria-hidden="true" />
        <span class="pointer-events-none absolute right-5 top-3 animate-floaty text-2xl opacity-70" aria-hidden="true">🐾</span>
        <span
          class="pointer-events-none absolute bottom-2 right-1/3 animate-floaty text-lg opacity-60"
          style="animation-delay: -2.5s"
          aria-hidden="true"
          >✨</span
        >

        <div class="relative flex flex-col gap-3 px-4 py-4 sm:px-6 sm:py-5 lg:flex-row lg:items-center lg:gap-6">
          <div class="min-w-0 lg:flex-1">
            <p class="text-lg font-bold text-text sm:text-xl">欢迎来到喵圈～</p>
            <p class="mt-1 text-xs text-text-muted sm:text-sm">
              和马卡龙色一起追番、晒手办、聊日常 🌈
            </p>
          </div>

          <!-- 站外动漫入口 -->
          <div class="flex flex-wrap items-center gap-2">
            <a
              href="https://ac.qq.com/"
              target="_blank"
              rel="noopener noreferrer"
              class="group inline-flex items-center gap-2 rounded-2xl border border-border bg-surface px-3 py-2 text-sm font-medium text-text shadow-card transition hover:-translate-y-0.5 hover:border-primary"
              title="腾讯动漫（新标签页打开）"
            >
              <span class="grid h-8 w-8 place-items-center rounded-xl bg-primary-soft text-base">🐧</span>
              <span>腾讯动漫</span>
              <span class="text-xs text-text-muted transition group-hover:translate-x-0.5">↗</span>
            </a>
            <a
              href="https://www.bilibili.com/anime/"
              target="_blank"
              rel="noopener noreferrer"
              class="group inline-flex items-center gap-2 rounded-2xl border border-border bg-surface px-3 py-2 text-sm font-medium text-text shadow-card transition hover:-translate-y-0.5 hover:border-primary"
              title="B站番剧（新标签页打开）"
            >
              <span class="grid h-8 w-8 place-items-center rounded-xl bg-primary-soft text-base">📺</span>
              <span>B站番剧</span>
              <span class="text-xs text-text-muted transition group-hover:translate-x-0.5">↗</span>
            </a>
          </div>

          <!-- 站内公告 -->
          <div class="rounded-2xl border border-border bg-surface px-3.5 py-2.5 lg:w-[320px] lg:shrink-0">
            <p class="flex items-center gap-1.5 text-xs font-semibold text-text">📢 站内公告</p>
            <p class="mt-1 line-clamp-2 text-xs leading-relaxed text-text-muted">
              欢迎来到喵圈！发帖请遵守版规，友善交流，不要剧透哦～ 有问题可以到「水区闲聊」提问。
            </p>
          </div>
        </div>
      </div>
    </section>

    <main class="mx-auto max-w-7xl px-4 py-5 sm:py-6">
      <router-view />
    </main>

    <footer class="mx-auto max-w-7xl px-4 pb-10 pt-4 text-center text-xs text-text-muted">
      <span class="cat-paw mr-1 text-primary" aria-hidden="true" />
      喵圈 · 用心做出的二次元可爱风论坛
    </footer>

    <!-- 换肤云端保存失败提示 -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="cloudNotice"
        class="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full border border-border bg-surface px-4 py-2 text-sm text-text shadow-card"
      >
        🎨 {{ cloudNotice }}
      </div>
    </Transition>
  </div>
</template>
