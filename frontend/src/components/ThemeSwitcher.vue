<script setup lang="ts">
import { ref } from 'vue'

import { useClickOutside } from '@/composables/useClickOutside'
import { useTheme } from '@/composables/useTheme'

const { themes, current, setTheme } = useTheme()

const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)

useClickOutside(rootRef, () => {
  open.value = false
})

function pick(code: string): void {
  setTheme(code)
  open.value = false
}
</script>

<template>
  <div ref="rootRef" class="relative shrink-0">
    <button
      type="button"
      class="topbar-icon flex items-center gap-1.5 rounded-full border border-border bg-surface-2 px-3 py-2 text-sm text-text transition hover:shadow-card"
      title="切换主题"
      @click="open = !open"
    >
      <span>{{ current.emoji }}</span>
      <span class="theme-name hidden md:inline">{{ current.name }}</span>
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <div
        v-if="open"
        class="theme-panel absolute right-0 mt-2 w-44 overflow-hidden rounded-2xl border border-border bg-surface p-1.5 shadow-card"
      >
        <p class="px-3 py-1.5 text-xs text-text-muted">选择主题皮肤</p>
        <button
          v-for="item in themes"
          :key="item.code"
          type="button"
          class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition hover:bg-primary-soft"
          :class="item.code === current.code ? 'text-primary font-semibold' : 'text-text'"
          @click="pick(item.code)"
        >
          <!-- 用 data-theme 作用域取到该皮肤自己的 --color-primary，避免硬编码十六进制 -->
          <span
            :data-theme="item.code"
            class="h-4 w-4 shrink-0 rounded-full border border-border bg-primary"
          />
          <span class="flex-1">{{ item.emoji }} {{ item.name }}</span>
          <span v-if="item.code === current.code" class="text-xs">✓</span>
        </button>
      </div>
    </Transition>
  </div>
</template>
