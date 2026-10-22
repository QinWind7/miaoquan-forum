<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
    <!-- 渐变背景走 --gradient-hero，随主题切换 -->
    <div class="absolute inset-0 -z-10" :style="{ background: 'var(--gradient-hero)' }" />
    <span class="absolute left-[12%] top-[16%] -z-10 animate-floaty text-3xl opacity-70">🐾</span>
    <span class="absolute right-[14%] top-[24%] -z-10 animate-floaty text-3xl opacity-70">🐱</span>
    <span class="absolute bottom-[14%] left-[20%] -z-10 animate-floaty text-3xl opacity-70">🐾</span>

    <div class="w-full max-w-md">
      <div class="cute-card animate-fade-in-up p-7 sm:p-9">
        <div class="mb-6 text-center">
          <RouterLink to="/" class="inline-flex items-center gap-2 text-2xl font-bold text-primary">
            <span>🐾</span>
            <span class="cat-ears">喵圈</span>
          </RouterLink>
          <p class="mt-2 text-sm text-text-muted">二次元同好会 · 一起追番一起玩</p>
        </div>
        <router-view />
      </div>
      <div class="mt-5 text-center">
        <RouterLink
          to="/"
          class="text-sm text-text-muted transition hover:text-primary"
        >
          ← 回到首页逛逛
        </RouterLink>
      </div>
    </div>
  </div>
</template>
