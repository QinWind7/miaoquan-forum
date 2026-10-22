import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'

import { fetchMyTheme, updateMyTheme } from '@/api/theme'
import { THEME_PRESETS, useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'

/**
 * 把主题写到 <html data-theme> 并同步 localStorage。
 * index.html 的内联脚本读的就是同一份 localStorage 记录（key=theme）。
 */
export function applyTheme(code: string): void {
  document.documentElement.dataset.theme = code
  try {
    localStorage.setItem('theme', JSON.stringify({ code }))
  } catch {
    // 隐私模式 / 禁用存储时忽略
  }
}

/** 云端保存失败时的一次性提示文案（全局共享，切肤入口与布局都能读到）。 */
const cloudNotice = ref('')
let noticeTimer: ReturnType<typeof setTimeout> | undefined

function showCloudNotice(text: string): void {
  cloudNotice.value = text
  if (noticeTimer) clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    cloudNotice.value = ''
  }, 3200)
}

export function useTheme() {
  const store = useThemeStore()
  const userStore = useUserStore()
  const { code } = storeToRefs(store)

  const current = computed(
    () => THEME_PRESETS.find((item) => item.code === code.value) ?? THEME_PRESETS[0],
  )

  /**
   * 切换皮肤：本地立即生效；已登录时再 PUT 到服务端。
   * 服务端失败不影响本地视觉，只提示一句，避免界面状态错乱。
   */
  async function setTheme(next: string): Promise<void> {
    store.setTheme(next)
    applyTheme(store.code)

    if (!userStore.isLoggedIn) return
    try {
      await updateMyTheme(store.code)
    } catch {
      showCloudNotice('皮肤已本地切换，云端保存失败')
    }
  }

  /**
   * 登录成功 / fetchMe 后拉取云端偏好：
   * 返回了 code 就用它覆盖本地主题，返回 null 则保持本地不动。
   */
  async function syncFromServer(): Promise<void> {
    try {
      const data = await fetchMyTheme()
      if (data.theme && THEME_PRESETS.some((item) => item.code === data.theme)) {
        store.setTheme(data.theme)
        applyTheme(store.code)
      }
    } catch {
      // 拉取失败不打扰用户，继续用本地主题
    }
  }

  /** 应用启动时把持久化的主题重新刷到 <html> 上。 */
  function initTheme(): void {
    applyTheme(store.code)
  }

  return {
    themes: THEME_PRESETS,
    code,
    current,
    isDark: computed(() => current.value.isDark),
    cloudNotice,
    setTheme,
    syncFromServer,
    initTheme,
    applyTheme,
  }
}
