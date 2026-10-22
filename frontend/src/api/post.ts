import request from './request'
import type {
  CreatePostPayload,
  LikeResult,
  LikedPost,
  Paginated,
  Post,
  PostDetail,
  PostWriteResult,
  UpdatePostPayload,
  UploadResult,
} from './types'

export type PostOrdering =
  | '-created_at'
  | '-like_count'
  | '-view_count'
  | '-comment_count'
  | '-last_comment_at'

export interface PostQuery {
  board?: string
  page?: number
  page_size?: number
  ordering?: PostOrdering
  search?: string
  is_essence?: boolean
}

export interface PageQuery {
  page?: number
  page_size?: number
}

/**
 * 帖子列表：分页接口，响应为 DRF 标准结构 { count, next, previous, results }。
 */
export async function fetchPosts(params: PostQuery = {}): Promise<Paginated<Post>> {
  const { data } = await request.get<Paginated<Post>>('/posts/', { params })
  return data
}

/**
 * 站长推荐：后端取 is_essence=True（精华帖）作为推荐位数据源。
 * 项目没有独立的推荐表，推荐位 = 精华帖，避免两处数据源不一致。
 */
export async function fetchRecommendedPosts(limit = 3): Promise<Post[]> {
  const { data } = await request.get<Paginated<Post>>('/posts/', {
    params: { is_essence: true, page_size: limit, ordering: '-created_at' },
  })
  return data.results
}

/**
 * 帖子详情：注意后端每次 GET 都会累加浏览数（30 分钟去重），
 * 所以详情页只请求一次，不要轮询。
 */
export async function fetchPost(id: number | string): Promise<PostDetail> {
  const { data } = await request.get<PostDetail>(`/posts/${id}/`)
  return data
}

/** 发帖（需登录），成功 201 返回写入后的帖子字段（含 id）。 */
export async function createPost(payload: CreatePostPayload): Promise<PostWriteResult> {
  const { data } = await request.post<PostWriteResult>('/posts/', payload)
  return data
}

/** 编辑帖子（仅作者，字段不含 board）。 */
export async function updatePost(
  id: number | string,
  payload: UpdatePostPayload,
): Promise<PostWriteResult> {
  const { data } = await request.patch<PostWriteResult>(`/posts/${id}/`, payload)
  return data
}

/** 删除帖子（软删，204）。 */
export async function deletePost(id: number | string): Promise<void> {
  await request.delete(`/posts/${id}/`)
}

/** 点赞 / 取消点赞（需登录，幂等），返回 { liked, like_count }。 */
export async function likePost(id: number): Promise<LikeResult> {
  const { data } = await request.post<LikeResult>(`/posts/${id}/like/`)
  return data
}

/** 我发表的帖子（需登录，分页）。 */
export async function fetchMyPosts(params: PageQuery = {}): Promise<Paginated<Post>> {
  const { data } = await request.get<Paginated<Post>>('/users/my/posts/', { params })
  return data
}

/** 我点赞过的帖子（需登录，分页，按点赞时间倒序，元素多 liked_at）。 */
export async function fetchMyLikes(params: PageQuery = {}): Promise<Paginated<LikedPost>> {
  const { data } = await request.get<Paginated<LikedPost>>('/users/my/likes/', { params })
  return data
}

/**
 * 上传单张图片（需登录，multipart 字段名 image），返回 { url: '/media/...' }。
 * 不显式设置 Content-Type：浏览器会自动带上 multipart 的 boundary。
 */
export async function uploadImage(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('image', file)
  const { data } = await request.post<UploadResult>('/uploads/image/', form)
  return data
}
