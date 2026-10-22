import { onBeforeUnmount, onMounted, type Ref } from 'vue'

/** 点击元素外部时触发回调（用于头像、主题菜单的收起）。 */
export function useClickOutside(elRef: Ref<HTMLElement | null>, handler: () => void): void {
  function onClick(event: MouseEvent): void {
    const el = elRef.value
    if (el && !el.contains(event.target as Node)) handler()
  }

  onMounted(() => document.addEventListener('click', onClick))
  onBeforeUnmount(() => document.removeEventListener('click', onClick))
}
