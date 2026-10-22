<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { fetchBoards } from '@/api/board'
import { createPost, fetchPost, updatePost, uploadImage } from '@/api/post'
import { ApiError } from '@/api/request'
import type { Board, PostImage } from '@/api/types'

const MAX_IMAGES = 9
const MAX_IMAGE_MB = 5
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.name === 'post-edit')
const editId = computed(() => Number(route.params.id))

const boards = ref<Board[]>([])
const board = ref('')
const title = ref('')
const content = ref('')
const images = ref<PostImage[]>([])

const prefillLoading = ref(true)
const submitting = ref(false)
const uploading = ref(false)
const loadError = ref('')
const errorMessage = ref('')
const fieldErrors = ref<Record<string, string>>({})
const fileInput = ref<HTMLInputElement | null>(null)

const currentBoard = computed(() => boards.value.find((item) => item.slug === board.value) ?? null)
const canAddMore = computed(() => images.value.length < MAX_IMAGES)

async function loadBoards(): Promise<void> {
  try {
    boards.value = await fetchBoards()
  } catch {
    boards.value = []
  }
}

async function loadForEdit(): Promise<void> {
  try {
    const post = await fetchPost(editId.value)
    board.value = post.board.slug
    title.value = post.title
    content.value = post.content
    images.value = [...(post.images ?? [])]
    if (!boards.value.some((item) => item.slug === post.board.slug)) {
      boards.value = [
        { ...post.board, description: '', cover: null, post_count: 0, sort_order: 0 },
        ...boards.value,
      ]
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '帖子加载失败，请稍后重试'
  }
}

/** 读一次原图尺寸，随 images 一起提交，缺省用 0 兜底。 */
function measure(url: string): Promise<{ w: number; h: number }> {
  return new Promise((resolve) => {
    const image = new Image()
    image.onload = () => resolve({ w: image.naturalWidth, h: image.naturalHeight })
    image.onerror = () => resolve({ w: 0, h: 0 })
    image.src = url
  })
}

async function onPickImages(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  input.value = ''
  if (!files.length) return

  fieldErrors.value = { ...fieldErrors.value, images: '' }
  uploading.value = true
  try {
    for (const file of files) {
      if (images.value.length >= MAX_IMAGES) {
        fieldErrors.value = { ...fieldErrors.value, images: `最多上传 ${MAX_IMAGES} 张图片` }
        break
      }
      if (!ALLOWED_TYPES.includes(file.type)) {
        fieldErrors.value = { ...fieldErrors.value, images: '仅支持 jpg / png / webp / gif 格式' }
        continue
      }
      if (file.size > MAX_IMAGE_MB * 1024 * 1024) {
        fieldErrors.value = { ...fieldErrors.value, images: `单张图片不能超过 ${MAX_IMAGE_MB}MB` }
        continue
      }
      try {
        const result = await uploadImage(file)
        const size = await measure(result.url)
        images.value.push({ url: result.url, w: size.w, h: size.h })
      } catch (error) {
        fieldErrors.value = {
          ...fieldErrors.value,
          images: error instanceof ApiError ? error.message : '图片上传失败，请稍后重试',
        }
      }
    }
  } finally {
    uploading.value = false
  }
}

function removeImage(index: number): void {
  images.value.splice(index, 1)
}

function pickError(errors: Record<string, unknown> | null, key: string): string {
  if (!errors) return ''
  const value = errors[key]
  if (typeof value === 'string') return value
  if (Array.isArray(value) && value.length) return String(value[0])
  return ''
}

function validate(): boolean {
  const next: Record<string, string> = {}
  if (!isEdit.value && !board.value) next.board = '请选择一个分区'
  const trimmedTitle = title.value.trim()
  if (!trimmedTitle) next.title = '标题不能为空'
  else if (trimmedTitle.length < 2 || trimmedTitle.length > 120) next.title = '标题长度需为 2~120 字'
  if (!content.value.trim()) next.content = '正文不能为空'
  fieldErrors.value = next
  return Object.keys(next).length === 0
}

async function onSubmit(): Promise<void> {
  errorMessage.value = ''
  if (!validate()) return

  submitting.value = true
  try {
    const payload = {
      title: title.value.trim(),
      content: content.value,
      images: images.value,
    }
    const result = isEdit.value
      ? await updatePost(editId.value, payload)
      : await createPost({ ...payload, board: board.value })
    router.replace({ name: 'post-detail', params: { id: result.id } })
  } catch (error) {
    if (error instanceof ApiError) {
      fieldErrors.value = {
        board: pickError(error.errors, 'board'),
        title: pickError(error.errors, 'title'),
        content: pickError(error.errors, 'content'),
        images: pickError(error.errors, 'images'),
      }
      errorMessage.value = error.message
    } else {
      errorMessage.value = '提交失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadBoards()
  if (isEdit.value) await loadForEdit()
  prefillLoading.value = false
})
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <div class="cute-card p-5 sm:p-6">
      <div class="mb-5 flex items-center justify-between gap-2">
        <div>
          <h1 class="text-lg font-bold text-text">{{ isEdit ? '✏️ 编辑帖子' : '✏️ 发布新帖' }}</h1>
          <p class="mt-0.5 text-xs text-text-muted">
            {{ isEdit ? '修改后保存，分区保持不变哦～' : '和大家分享你的二次元日常吧～' }}
          </p>
        </div>
        <RouterLink
          :to="isEdit ? { name: 'post-detail', params: { id: editId } } : { name: 'home' }"
          class="shrink-0 text-sm text-text-muted transition hover:text-primary"
        >
          ← 返回
        </RouterLink>
      </div>

      <div v-if="prefillLoading" class="space-y-4">
        <div class="h-11 w-full animate-pulse rounded-2xl bg-surface-2" />
        <div class="h-11 w-full animate-pulse rounded-2xl bg-surface-2" />
        <div class="h-40 w-full animate-pulse rounded-2xl bg-surface-2" />
      </div>

      <div
        v-else-if="loadError"
        class="flex flex-col items-center gap-3 py-10 text-center"
      >
        <div class="text-4xl">😢</div>
        <p class="text-sm font-semibold text-text">帖子加载失败了</p>
        <p class="text-sm text-text-muted">{{ loadError }}</p>
        <RouterLink :to="{ name: 'home' }" class="cute-btn bg-primary text-white">
          🏠 回首页
        </RouterLink>
      </div>

      <form v-else class="space-y-4" @submit.prevent="onSubmit">
        <!-- 分区：编辑模式不显示选择 -->
        <div v-if="!isEdit">
          <label for="board" class="mb-1.5 block text-sm font-medium text-text">分区 <span class="text-primary">*</span></label>
          <select id="board" v-model="board" class="cute-input">
            <option value="" disabled>请选择分区</option>
            <option v-for="item in boards" :key="item.id" :value="item.slug">
              {{ item.icon }} {{ item.name }}
            </option>
          </select>
          <p v-if="fieldErrors.board" class="mt-1 text-xs text-primary">😿 {{ fieldErrors.board }}</p>
        </div>
        <div v-else-if="currentBoard" class="flex items-center gap-2 text-sm text-text">
          <span class="text-text-muted">分区：</span>
          <span
            class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
            :style="{ color: currentBoard.color, backgroundColor: currentBoard.color + '22' }"
          >
            {{ currentBoard.icon }} {{ currentBoard.name }}
          </span>
        </div>

        <!-- 标题 -->
        <div>
          <label for="title" class="mb-1.5 block text-sm font-medium text-text">标题 <span class="text-primary">*</span></label>
          <input
            id="title"
            v-model="title"
            type="text"
            maxlength="120"
            placeholder="给帖子起个可爱的标题吧～"
            class="cute-input"
          />
          <div class="mt-1 flex items-center justify-between">
            <p v-if="fieldErrors.title" class="text-xs text-primary">😿 {{ fieldErrors.title }}</p>
            <span class="ml-auto text-[11px] text-text-muted">{{ title.length }} / 120</span>
          </div>
        </div>

        <!-- 正文 -->
        <div>
          <label for="content" class="mb-1.5 block text-sm font-medium text-text">正文 <span class="text-primary">*</span></label>
          <textarea
            id="content"
            v-model="content"
            rows="12"
            placeholder="支持 Markdown，尽情发挥吧～"
            class="cute-input resize-y font-mono text-[13px] leading-relaxed"
          />
          <div class="mt-1 flex items-center justify-between">
            <p v-if="fieldErrors.content" class="text-xs text-primary">😿 {{ fieldErrors.content }}</p>
            <p class="ml-auto text-[11px] text-text-muted">支持 Markdown：# 标题、**加粗**、- 列表、![图](链接)</p>
          </div>
        </div>

        <!-- 图片上传 -->
        <div>
          <div class="mb-1.5 flex items-center justify-between">
            <span class="text-sm font-medium text-text">配图（最多 {{ MAX_IMAGES }} 张）</span>
            <button
              type="button"
              class="cute-btn border border-border bg-surface-2 text-text hover:shadow-card disabled:opacity-50"
              :disabled="uploading || !canAddMore"
              @click="fileInput?.click()"
            >
              {{ uploading ? '上传中…' : '＋ 添加图片' }}
            </button>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            multiple
            class="hidden"
            @change="onPickImages"
          />
          <p v-if="fieldErrors.images" class="text-xs text-primary">😿 {{ fieldErrors.images }}</p>

          <div v-if="images.length" class="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-4">
            <div
              v-for="(image, index) in images"
              :key="image.url + index"
              class="group relative overflow-hidden rounded-2xl border border-border"
            >
              <img :src="image.url" alt="配图预览" class="aspect-square w-full object-cover" />
              <button
                type="button"
                class="absolute right-1 top-1 grid h-6 w-6 place-items-center rounded-full bg-surface text-xs text-text shadow-card transition hover:scale-110"
                title="移除"
                @click="removeImage(index)"
              >
                ✕
              </button>
            </div>
          </div>
        </div>

        <p v-if="errorMessage" class="rounded-2xl bg-primary-soft px-4 py-2.5 text-sm text-text">
          😿 {{ errorMessage }}
        </p>

        <div class="flex items-center justify-end gap-3 pt-1">
          <RouterLink
            :to="isEdit ? { name: 'post-detail', params: { id: editId } } : { name: 'home' }"
            class="cute-btn border border-border bg-surface text-text hover:shadow-card"
          >
            取消
          </RouterLink>
          <button
            type="submit"
            class="cute-btn bg-primary font-semibold text-white hover:shadow-card disabled:opacity-60"
            :disabled="submitting || uploading"
          >
            {{ submitting ? '提交中…' : isEdit ? '保存修改' : '发布帖子' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
