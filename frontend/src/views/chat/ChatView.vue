<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { fetchConversations, fetchMessages, sendMessage } from '@/api/chat'
import { fetchFriends } from '@/api/social'
import type { ChatMessage, LastChatMessage, UserBrief } from '@/api/types'
import { useUserStore } from '@/stores/user'
import { fromNow } from '@/utils/format'

/** 左侧栏的一行：有聊天记录的会话，或还没聊过天的好友。 */
interface SidebarItem {
  partner: UserBrief
  last: LastChatMessage | null
  unread: number
  at: string
}

const POLL_INTERVAL = 5000

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const sidebar = ref<SidebarItem[]>([])
const sidebarLoading = ref(true)
const sidebarError = ref('')

const activeId = ref<number | null>(null)
const activePartner = ref<UserBrief | null>(null)
const messages = ref<ChatMessage[]>([])
const messagesLoading = ref(false)
const messagesError = ref('')

const draft = ref('')
const sending = ref(false)
const sendError = ref('')

const listRef = ref<HTMLElement | null>(null)
const polling = ref(false)
let timer: ReturnType<typeof setInterval> | undefined

const myId = computed(() => userStore.user?.id ?? 0)

async function loadSidebar(): Promise<void> {
  sidebarLoading.value = true
  sidebarError.value = ''
  try {
    const [conversations, friends] = await Promise.all([
      fetchConversations(),
      fetchFriends({ page_size: 100 }),
    ])

    const items: SidebarItem[] = conversations.map((conv) => ({
      partner: conv.partner,
      last: conv.last_message,
      unread: conv.unread_count,
      at: conv.last_at,
    }))

    // 已经是好友但还没聊过天的，也放进列表，方便主动发起
    const talked = new Set(conversations.map((conv) => conv.partner.id))
    for (const friend of friends.results) {
      if (talked.has(friend.user.id)) continue
      items.push({ partner: friend.user, last: null, unread: 0, at: '' })
    }

    sidebar.value = items
  } catch (error) {
    sidebarError.value = error instanceof Error ? error.message : '会话列表加载失败'
  } finally {
    sidebarLoading.value = false
  }
}

function scrollToBottom(): void {
  const el = listRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

async function openChat(partner: UserBrief | number): Promise<void> {
  const id = typeof partner === 'number' ? partner : partner.id
  if (!id || id === myId.value) return

  activeId.value = id
  if (typeof partner !== 'number') {
    activePartner.value = partner
  } else {
    const found = sidebar.value.find((item) => item.partner.id === id)
    activePartner.value = found ? found.partner : null
  }

  messagesLoading.value = true
  messagesError.value = ''
  sendError.value = ''
  try {
    messages.value = await fetchMessages(id)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    messages.value = []
    messagesError.value = error instanceof Error ? error.message : '聊天记录加载失败'
  } finally {
    messagesLoading.value = false
  }

  // 用 replace：切换会话不往浏览器历史里塞垃圾记录
  if (Number(route.query.user) !== id) {
    void router.replace({ name: 'chat', query: { user: String(id) } })
  }
  void loadSidebar()
}

function closeChat(): void {
  activeId.value = null
  activePartner.value = null
  messages.value = []
  void router.replace({ name: 'chat' })
}

/** 轮询：只拉比本地最后一条更新的消息，避免整段重载。 */
async function poll(): Promise<void> {
  if (!userStore.isLoggedIn || polling.value || !activeId.value) return
  polling.value = true
  const id = activeId.value
  const lastId = messages.value.length ? messages.value[messages.value.length - 1].id : 0

  try {
    const fresh = await fetchMessages(id, lastId)
    if (id !== activeId.value) return
    if (fresh.length) {
      messages.value.push(...fresh)
      await nextTick()
      scrollToBottom()
    }
    await loadSidebar()
  } catch {
    // 轮询失败静默处理，下一轮再试
  } finally {
    polling.value = false
  }
}

async function onSend(): Promise<void> {
  const content = draft.value.trim()
  if (!content || !activeId.value || sending.value) return

  sending.value = true
  sendError.value = ''
  try {
    const message = await sendMessage(activeId.value, content)
    messages.value.push(message)
    draft.value = ''
    await nextTick()
    scrollToBottom()
    void loadSidebar()
  } catch (error) {
    sendError.value = error instanceof Error ? error.message : '发送失败，请稍后重试'
  } finally {
    sending.value = false
  }
}

/** 回车发送，Shift+回车换行。 */
function onKeydown(event: KeyboardEvent): void {
  if (event.shiftKey || event.isComposing) return
  event.preventDefault()
  void onSend()
}

watch(
  () => route.query.user,
  (value) => {
    const id = Number(value)
    if (!id || id === activeId.value) return
    if (sidebar.value.length) {
      void openChat(id)
    }
  },
  { immediate: true },
)

// 侧栏先到位再按 query 打开，避免打开后又被空列表覆盖
watch(sidebar, () => {
  const id = Number(route.query.user)
  if (id && id !== activeId.value) void openChat(id)
}, { once: true })

onMounted(() => {
  void loadSidebar()
  timer = setInterval(() => void poll(), POLL_INTERVAL)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <div class="cute-card flex h-[68vh] min-h-[440px] overflow-hidden p-0">
      <!-- 左：会话 / 好友列表 -->
      <aside
        class="min-h-0 w-full shrink-0 flex-col border-r border-border bg-surface-2/40 sm:flex sm:w-72"
        :class="activeId ? 'hidden' : 'flex'"
      >
        <div class="border-b border-border px-4 py-3">
          <p class="text-sm font-semibold text-text">💬 我的私聊</p>
          <p class="mt-0.5 text-[11px] text-text-muted">好友之间才能聊天哦～</p>
        </div>

        <div v-if="sidebarLoading" class="space-y-2 p-3">
          <div v-for="n in 4" :key="n" class="h-12 animate-pulse rounded-2xl bg-surface" />
        </div>

        <div v-else-if="sidebarError" class="flex flex-col items-center gap-2 px-4 py-10 text-center">
          <div class="text-4xl">😿</div>
          <p class="text-xs text-text-muted">{{ sidebarError }}</p>
          <button type="button" class="cute-btn bg-primary text-xs text-white" @click="loadSidebar">
            再试一次
          </button>
        </div>

        <div
          v-else-if="!sidebar.length"
          class="flex flex-col items-center gap-2 px-4 py-12 text-center"
        >
          <div class="text-4xl">🐾</div>
          <p class="text-sm font-semibold text-text">还没有好友可以聊天</p>
          <p class="text-[11px] text-text-muted">先去别人的主页加个好友吧～</p>
        </div>

        <ul v-else class="min-h-0 flex-1 overflow-y-auto p-2">
          <li v-for="item in sidebar" :key="item.partner.id">
            <button
              type="button"
              class="flex w-full items-center gap-2.5 rounded-2xl px-2 py-2 text-left transition hover:bg-primary-soft"
              :class="activeId === item.partner.id ? 'bg-primary-soft' : ''"
              @click="openChat(item.partner)"
            >
              <span class="relative shrink-0">
                <img
                  v-if="item.partner.avatar"
                  :src="item.partner.avatar"
                  :alt="item.partner.display_name"
                  class="h-10 w-10 rounded-full object-cover"
                />
                <span
                  v-else
                  class="grid h-10 w-10 place-items-center rounded-full bg-primary-soft text-sm font-bold text-text"
                >
                  {{ (item.partner.display_name || '喵').slice(0, 1) }}
                </span>
                <span
                  v-if="item.unread"
                  class="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-primary px-1 text-[10px] font-bold leading-none text-white"
                >
                  {{ item.unread > 99 ? '99+' : item.unread }}
                </span>
              </span>

              <span class="min-w-0 flex-1">
                <span class="flex items-baseline justify-between gap-2">
                  <span class="truncate text-sm font-semibold text-text">
                    {{ item.partner.display_name }}
                  </span>
                  <span class="shrink-0 text-[10px] text-text-muted">{{ fromNow(item.at) }}</span>
                </span>
                <span class="mt-0.5 block truncate text-[11px] text-text-muted">
                  <template v-if="item.last">
                    {{ item.last.from_me ? '我：' : '' }}{{ item.last.content }}
                  </template>
                  <template v-else>还没有聊过天，快打个招呼～</template>
                </span>
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <!-- 右：聊天窗口 -->
      <section
        class="min-h-0 min-w-0 flex-1 flex-col"
        :class="activeId ? 'flex' : 'hidden sm:flex'"
      >
        <template v-if="activePartner">
          <header class="flex items-center gap-2 border-b border-border px-3 py-2.5 sm:px-4">
            <button
              type="button"
              class="grid h-8 w-8 shrink-0 place-items-center rounded-full text-text-muted transition hover:bg-surface-2 sm:hidden"
              title="返回会话列表"
              @click="closeChat"
            >
              ‹
            </button>
            <RouterLink
              :to="{ name: 'user-profile', params: { id: activePartner.id } }"
              class="flex min-w-0 items-center gap-2"
            >
              <img
                v-if="activePartner.avatar"
                :src="activePartner.avatar"
                :alt="activePartner.display_name"
                class="h-8 w-8 rounded-full object-cover"
              />
              <span
                v-else
                class="grid h-8 w-8 place-items-center rounded-full bg-primary-soft text-xs font-bold text-text"
              >
                {{ (activePartner.display_name || '喵').slice(0, 1) }}
              </span>
              <span class="min-w-0">
                <span class="block truncate text-sm font-semibold text-text hover:text-primary">
                  {{ activePartner.display_name }}
                </span>
                <span class="block text-[10px] text-text-muted">Lv.{{ activePartner.level }}</span>
              </span>
            </RouterLink>
            <span class="ml-auto rounded-full bg-surface-2 px-2 py-0.5 text-[10px] text-text-muted">
              好友
            </span>
          </header>

          <div ref="listRef" class="min-h-0 flex-1 space-y-2 overflow-y-auto bg-bg/40 px-3 py-3 sm:px-4">
            <div v-if="messagesLoading" class="space-y-3">
              <div v-for="n in 3" :key="n" class="h-10 w-2/3 animate-pulse rounded-2xl bg-surface-2" />
            </div>

            <div
              v-else-if="messagesError"
              class="flex flex-col items-center gap-2 py-12 text-center"
            >
              <div class="text-4xl">😢</div>
              <p class="text-xs text-text-muted">{{ messagesError }}</p>
            </div>

            <template v-else>
              <p
                v-if="!messages.length"
                class="py-10 text-center text-xs text-text-muted"
              >
                还没有聊天记录，说点什么吧～ 🐾
              </p>

              <div
                v-for="message in messages"
                :key="message.id"
                class="flex items-end gap-2"
                :class="message.sender.id === myId ? 'flex-row-reverse' : ''"
              >
                <span
                  class="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary-soft text-[10px] font-bold text-text"
                >
                  {{ (message.sender.display_name || '喵').slice(0, 1) }}
                </span>
                <div class="min-w-0 max-w-[76%]">
                  <div
                    class="whitespace-pre-wrap break-words rounded-2xl px-3 py-2 text-sm shadow-card"
                    :class="
                      message.sender.id === myId
                        ? 'rounded-br-md bg-primary text-white'
                        : 'rounded-bl-md bg-surface text-text'
                    "
                  >
                    {{ message.content }}
                  </div>
                  <p
                    class="mt-0.5 text-[10px] text-text-muted"
                    :class="message.sender.id === myId ? 'text-right' : ''"
                  >
                    {{ fromNow(message.created_at) }}
                  </p>
                </div>
              </div>
            </template>
          </div>

          <div class="border-t border-border p-2.5 sm:p-3">
            <p v-if="sendError" class="mb-1.5 text-[11px] text-primary">😿 {{ sendError }}</p>
            <div class="flex items-end gap-2">
              <textarea
                v-model="draft"
                rows="1"
                maxlength="1000"
                placeholder="说点可爱的…（回车发送，Shift+回车换行）"
                class="cute-input max-h-28 min-h-[42px] flex-1 resize-none py-2.5 text-sm"
                @keydown.enter="onKeydown"
              />
              <button
                type="button"
                class="cute-btn h-[42px] shrink-0 bg-primary px-4 text-white hover:shadow-card disabled:opacity-50"
                :disabled="sending || !draft.trim()"
                @click="onSend"
              >
                {{ sending ? '发送中' : '发送' }}
              </button>
            </div>
          </div>
        </template>

        <div v-else class="flex flex-1 flex-col items-center justify-center gap-2 px-6 text-center">
          <div class="text-5xl">💌</div>
          <p class="text-base font-semibold text-text">选一位好友开始聊天吧～</p>
          <p class="text-xs text-text-muted">左侧列出了你的会话和好友，点一下就能开聊</p>
        </div>
      </section>
    </div>
  </div>
</template>
