<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { Post } from '@/api/types'
import PostLikeButton from '@/components/post/PostLikeButton.vue'
import { compactCount, fromNow } from '@/utils/format'

const props = defineProps<{ post: Post }>()
</script>

<template>
  <article
    class="cute-card group flex overflow-hidden transition duration-300 ease-out hover:-translate-y-1 hover:scale-[1.01] hover:border-primary"
  >
    <!-- 封面：无图时用渐变占位；点击进入详情 -->
    <RouterLink
      :to="{ name: 'post-detail', params: { id: props.post.id } }"
      class="relative h-28 w-24 shrink-0 sm:h-36 sm:w-44"
    >
      <img
        v-if="post.cover_image"
        :src="post.cover_image"
        :alt="post.title"
        class="h-full w-full object-cover"
        loading="lazy"
      />
      <div
        v-else
        class="grid h-full w-full place-items-center text-3xl"
        :style="{ background: 'var(--gradient-hero)' }"
      >
        {{ post.board.icon }}
      </div>
    </RouterLink>

    <div class="flex min-w-0 flex-1 flex-col p-4">
      <div class="mb-1.5 flex flex-wrap items-center gap-1.5">
        <span
          v-if="post.is_pinned"
          class="rounded-full bg-accent px-2 py-0.5 text-[11px] font-semibold text-text"
        >
          📌 置顶
        </span>
        <span
          v-if="post.is_essence"
          class="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-semibold text-text"
        >
          ✨ 精华
        </span>
        <span
          class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
          :style="{ color: post.board.color, backgroundColor: post.board.color + '22' }"
        >
          {{ post.board.icon }} {{ post.board.name }}
        </span>
      </div>

      <RouterLink :to="{ name: 'post-detail', params: { id: props.post.id } }" class="min-w-0">
        <h3 class="truncate text-base font-bold text-text transition group-hover:text-primary sm:text-lg">
          {{ post.title }}
        </h3>
        <p class="mt-1 line-clamp-2 text-sm leading-relaxed text-text-muted">
          {{ post.summary || '这个帖子还没有摘要，点进去看看吧～' }}
        </p>
      </RouterLink>

      <div class="mt-auto flex items-center justify-between gap-2 pt-3">
        <RouterLink
          :to="{ name: 'user-profile', params: { id: post.author.id } }"
          class="flex min-w-0 items-center gap-2 rounded-full transition hover:text-primary"
          :title="`查看 ${post.author.display_name} 的主页`"
        >
          <img
            v-if="post.author.avatar"
            :src="post.author.avatar"
            :alt="post.author.display_name"
            class="h-6 w-6 shrink-0 rounded-full object-cover"
          />
          <span
            v-else
            class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary-soft text-[11px] font-bold text-text"
          >
            {{ (post.author.display_name || '喵').slice(0, 1) }}
          </span>
          <span class="truncate text-xs text-text-muted transition hover:text-primary">
            {{ post.author.display_name }}
          </span>
          <span
            class="hidden shrink-0 rounded-full bg-surface-2 px-1.5 py-0.5 text-[10px] text-text-muted sm:inline"
          >
            Lv.{{ post.author.level }}
          </span>
        </RouterLink>

        <div class="flex shrink-0 items-center gap-2.5 text-xs text-text-muted sm:gap-3">
          <PostLikeButton :post="post" />
          <span class="flex items-center gap-1">👀 {{ compactCount(post.view_count) }}</span>
          <span class="flex items-center gap-1">💬 {{ compactCount(post.comment_count) }}</span>
          <span class="hidden sm:inline">{{ fromNow(post.created_at) }}</span>
        </div>
      </div>

      <!-- 供「我的点赞」等页面补充额外信息（如点赞时间 / 取消点赞） -->
      <slot name="extra" />
    </div>
  </article>
</template>
