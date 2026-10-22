<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 text-center">
    <div class="absolute inset-0 -z-10" :style="{ background: 'var(--gradient-hero)' }" />
    <span class="absolute left-[14%] top-[18%] -z-10 animate-floaty text-3xl opacity-70">🐾</span>
    <span class="absolute bottom-[16%] right-[16%] -z-10 animate-floaty text-3xl opacity-70">🐱</span>

    <div class="cute-card animate-fade-in-up max-w-md p-8 sm:p-10">
      <p class="text-6xl">🌀</p>
      <h1 class="mt-4 text-4xl font-bold text-primary">404</h1>
      <p class="mt-2 text-base font-semibold text-text">这个页面好像走丢了呢～</p>
      <p class="mt-1 text-sm text-text-muted">它可能去找小猫咪玩了，我们先回首页看看吧！</p>
      <RouterLink to="/" class="cute-btn mt-6 bg-primary font-semibold text-white hover:shadow-card">
        🏠 回到首页
      </RouterLink>
    </div>
  </div>
</template>
