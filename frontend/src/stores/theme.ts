import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ThemePreset {
  code: string
  name: string
  emoji: string
  isDark: boolean
}

/** 内置 4 套皮肤，code 与后端 themes_themes.code 对齐。 */
export const THEME_PRESETS: ThemePreset[] = [
  { code: 'sakura', name: '樱花粉', emoji: '🌸', isDark: false },
  { code: 'ocean', name: '天空蓝', emoji: '🌊', isDark: false },
  { code: 'midnight', name: '深夜黑', emoji: '🌙', isDark: true },
  { code: 'matcha', name: '抹茶绿', emoji: '🍵', isDark: false },
]

export const DEFAULT_THEME = 'sakura'

export const useThemeStore = defineStore(
  'theme',
  () => {
    const code = ref<string>(DEFAULT_THEME)

    function setTheme(next: string): void {
      if (THEME_PRESETS.some((item) => item.code === next)) {
        code.value = next
      }
    }

    return { code, setTheme }
  },
  // key 固定为 'theme'，index.html 的内联防白闪脚本读的就是这条记录
  { persist: { key: 'theme' } },
)
