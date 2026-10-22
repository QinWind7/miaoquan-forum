<script setup lang="ts">
withDefaults(
  defineProps<{
    open: boolean
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
  }>(),
  {
    title: '确定要这么做吗？',
    message: '',
    confirmText: '确定',
    cancelText: '再想想',
    loading: false,
  },
)

defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
</script>

<template>
  <Transition
    enter-active-class="transition duration-150 ease-out"
    enter-from-class="opacity-0"
    leave-active-class="transition duration-100 ease-in"
    leave-to-class="opacity-0"
  >
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div
        class="absolute inset-0 backdrop-blur-sm"
        :style="{ backgroundColor: 'var(--color-text)', opacity: 0.28 }"
        @click="$emit('cancel')"
      />
      <div class="cute-card animate-fade-in-up relative z-10 w-full max-w-sm p-6 text-center">
        <p class="text-4xl">🥺</p>
        <h3 class="mt-3 text-base font-bold text-text">{{ title }}</h3>
        <p v-if="message" class="mt-1.5 text-sm leading-relaxed text-text-muted">{{ message }}</p>
        <div class="mt-6 flex justify-center gap-3">
          <button
            type="button"
            class="cute-btn border border-border bg-surface-2 text-text hover:shadow-card disabled:opacity-50"
            :disabled="loading"
            @click="$emit('cancel')"
          >
            {{ cancelText }}
          </button>
          <button
            type="button"
            class="cute-btn bg-primary font-semibold text-white hover:brightness-105 hover:shadow-card disabled:opacity-60"
            :disabled="loading"
            @click="$emit('confirm')"
          >
            {{ loading ? '处理中…' : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
