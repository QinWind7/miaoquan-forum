<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ page: number; totalPages: number }>()

const emit = defineEmits<{ (e: 'change', page: number): void }>()

const pageNumbers = computed(() => {
  const start = Math.max(1, props.page - 2)
  const end = Math.min(props.totalPages, start + 4)
  const numbers: number[] = []
  for (let i = start; i <= end; i += 1) numbers.push(i)
  return numbers
})

function go(target: number): void {
  if (target < 1 || target > props.totalPages || target === props.page) return
  emit('change', target)
}
</script>

<template>
  <div v-if="totalPages > 1" class="mt-5 flex items-center justify-center gap-2">
    <button
      type="button"
      class="cute-btn border border-border bg-surface text-text disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="page <= 1"
      @click="go(page - 1)"
    >
      上一页
    </button>
    <button
      v-for="n in pageNumbers"
      :key="n"
      type="button"
      class="h-9 w-9 rounded-full text-sm transition"
      :class="n === page ? 'bg-primary font-semibold text-white' : 'bg-surface-2 text-text hover:bg-primary-soft'"
      @click="go(n)"
    >
      {{ n }}
    </button>
    <button
      type="button"
      class="cute-btn border border-border bg-surface text-text disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="page >= totalPages"
      @click="go(page + 1)"
    >
      下一页
    </button>
  </div>
</template>
