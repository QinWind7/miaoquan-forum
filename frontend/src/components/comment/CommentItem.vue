<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { deleteComment, likeComment } from '@/api/comment'
import type { Comment, CommentReply, UserBrief } from '@/api/types'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useUserStore } from '@/stores/user'
import { compactCount, fromNow } from '@/utils/format'

import CommentEditor from './CommentEditor.vue'

const props = withDefaults(
  defineProps<{
    comment: Comment | CommentReply
    postId: number
    isReply?: boolean
  }>(),
  { isReply: false },
)

const emit = defineEmits<{
  (e: 'changed', delta: number): void
  (e: 'request-reply', comment: CommentReply): void
}>()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

/** 只有一级评论拥有 replies / replies_count。 */
const topComment = computed(() => props.comment as Comment)
const replies = computed<CommentReply[]>(() => (props.isReply ? [] : topComment.value.replies ?? []))

const liking = ref(false)
const deleting = ref(false)
const confirmOpen = ref(false)
const actionError = ref('')

const replyOpen = ref(false)
/** 被回复的目标（可能是本条，也可能是它下面的一条回复）。 */
const replyTarget = ref<{ id: number; user: UserBrief } | null>(null)

const canDelete = computed(
  () =>
    userStore.isLoggedIn &&
    !props.comment.is_deleted &&
    (userStore.user?.id === props.comment.author.id || Boolean(userStore.user?.is_staff)),
)

const authorName = computed(
  () => props.comment.author.display_name || props.comment.author.username,
)

function requireLogin(): boolean {
  if (userStore.isLoggedIn) return true
  router.push({ path: '/login', query: { redirect: route.fullPath } })
  return false
}

async function toggleLike(): Promise<void> {
  if (!requireLogin()) return
  if (liking.value) return
  liking.value = true

  const target = props.comment
  const prevLiked = target.is_liked
  const prevCount = target.like_count
  // 乐观更新，失败再回滚
  target.is_liked = !prevLiked
  target.like_count = prevCount + (prevLiked ? -1 : 1)

  try {
    const result = await likeComment(target.id)
    target.is_liked = result.liked
    target.like_count = result.like_count
  } catch {
    target.is_liked = prevLiked
    target.like_count = prevCount
  } finally {
    liking.value = false
  }
}

/** 二级回复的「回复」按钮：交给所属一级评论统一处理（两级封顶）。 */
function onReplyClick(): void {
  if (!requireLogin()) return
  if (props.isReply) {
    emit('request-reply', props.comment as CommentReply)
    return
  }
  replyTarget.value = { id: props.comment.id, user: props.comment.author }
  replyOpen.value = true
}

function openReplyForReply(reply: CommentReply): void {
  replyOpen.value = true
  replyTarget.value = { id: reply.id, user: reply.author }
}

/** 新回复由后端压平后返回完整评论对象，追加到本条回复列表尾部。 */
function onReplySubmitted(comment: Comment): void {
  const top = topComment.value
  if (!top.replies) top.replies = []
  top.replies.push(comment)
  top.replies_count += 1
  replyOpen.value = false
  replyTarget.value = null
  emit('changed', 1)
}

async function onDelete(): Promise<void> {
  if (deleting.value) return
  deleting.value = true
  actionError.value = ''
  try {
    await deleteComment(props.comment.id)
    // 后端软删后仍保留占位（子回复照常显示），这里同样只清空原文
    props.comment.is_deleted = true
    props.comment.content = ''
    confirmOpen.value = false
    emit('changed', -1)
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : '删除失败，请稍后重试'
    confirmOpen.value = false
  } finally {
    deleting.value = false
  }
}

function closeReply(): void {
  replyOpen.value = false
  replyTarget.value = null
}
</script>

<template>
  <div :class="isReply ? 'mt-3' : ''">
    <div class="flex gap-3">
      <RouterLink
        :to="{ name: 'user-profile', params: { id: comment.author.id } }"
        class="shrink-0"
        :title="`查看 ${authorName} 的主页`"
      >
        <img
          v-if="comment.author.avatar"
          :src="comment.author.avatar"
          :alt="authorName"
          class="h-9 w-9 shrink-0 rounded-full object-cover transition hover:opacity-85"
        />
        <span
          v-else
          class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary-soft text-sm font-bold text-text transition hover:opacity-85"
        >
          {{ authorName.slice(0, 1) }}
        </span>
      </RouterLink>

      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-1.5">
          <RouterLink
            :to="{ name: 'user-profile', params: { id: comment.author.id } }"
            class="text-sm font-semibold text-text transition hover:text-primary hover:underline"
          >
            {{ authorName }}
          </RouterLink>
          <span class="rounded-full bg-surface-2 px-1.5 py-0.5 text-[10px] text-text-muted">
            Lv.{{ comment.author.level }}
          </span>
          <span
            v-if="comment.author.is_staff"
            class="rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-semibold text-text"
          >
            管理员
          </span>
          <span class="text-[11px] text-text-muted">{{ fromNow(comment.created_at) }}</span>
        </div>

        <p v-if="comment.reply_to_user" class="mt-1 text-[11px] text-text-muted">
          回复
          <RouterLink
            :to="{ name: 'user-profile', params: { id: comment.reply_to_user.id } }"
            class="font-medium text-primary hover:underline"
          >
            @{{ comment.reply_to_user.display_name || comment.reply_to_user.username }}
          </RouterLink>
          ：
        </p>

        <p v-if="comment.is_deleted" class="mt-1 text-sm italic text-text-muted">该评论已删除</p>
        <p v-else class="mt-1 whitespace-pre-wrap break-words text-sm leading-relaxed text-text">
          {{ comment.content }}
        </p>

        <div class="mt-1.5 flex items-center gap-1">
          <button
            type="button"
            class="flex items-center gap-1 rounded-full px-2 py-1 text-xs transition hover:bg-primary-soft"
            :class="comment.is_liked ? 'font-semibold text-primary' : 'text-text-muted'"
            :disabled="comment.is_deleted"
            @click="toggleLike"
          >
            <span>{{ comment.is_liked ? '💗' : '🤍' }}</span>
            <span>{{ compactCount(comment.like_count) }}</span>
          </button>

          <button
            v-if="!comment.is_deleted"
            type="button"
            class="rounded-full px-2 py-1 text-xs text-text-muted transition hover:bg-primary-soft hover:text-primary"
            @click="onReplyClick"
          >
            回复
          </button>

          <button
            v-if="canDelete"
            type="button"
            class="rounded-full px-2 py-1 text-xs text-text-muted transition hover:bg-primary-soft hover:text-primary"
            @click="confirmOpen = true"
          >
            删除
          </button>

          <span v-if="!isReply && replies.length" class="ml-1 text-[11px] text-text-muted">
            · {{ replies.length }} 条回复
          </span>
        </div>

        <p v-if="actionError" class="mt-1 text-xs text-primary">😿 {{ actionError }}</p>

        <div v-if="!isReply && replyOpen" class="mt-3 rounded-2xl bg-surface-2 p-3">
          <CommentEditor
            :post-id="postId"
            :parent-id="replyTarget?.id"
            :reply-to-user="replyTarget?.user"
            @submitted="onReplySubmitted"
            @cancel="closeReply"
          />
        </div>

        <div v-if="!isReply && replies.length" class="mt-3 space-y-3 border-l-2 border-border pl-3">
          <CommentItem
            v-for="reply in replies"
            :key="reply.id"
            is-reply
            :comment="reply"
            :post-id="postId"
            @request-reply="openReplyForReply"
            @changed="(delta: number) => emit('changed', delta)"
          />
        </div>
      </div>
    </div>

    <ConfirmDialog
      :open="confirmOpen"
      title="要删掉这条评论吗？"
      message="删除后内容会变成「该评论已删除」，子回复会保留哦～"
      confirm-text="删除"
      :loading="deleting"
      @confirm="onDelete"
      @cancel="confirmOpen = false"
    />
  </div>
</template>
