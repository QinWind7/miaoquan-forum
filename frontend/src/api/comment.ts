import request from './request'
import type { Comment, CreateCommentPayload, LikeResult, Paginated } from './types'

export interface CommentQuery {
  page?: number
  page_size?: number
}

/**
 * 评论列表（匿名可读）：分页，count 只统计一级评论，回复内联在每条一级评论的 replies 里。
 */
export async function fetchComments(
  postId: number | string,
  params: CommentQuery = {},
): Promise<Paginated<Comment>> {
  const { data } = await request.get<Paginated<Comment>>(`/posts/${postId}/comments/`, {
    params,
  })
  return data
}

/**
 * 发表评论 / 回复（需登录）。
 * parent 传被回复评论的 id 即可，后端会把「回复的回复」压平到一级评论（两级封顶）。
 */
export async function createComment(
  postId: number | string,
  payload: CreateCommentPayload,
): Promise<Comment> {
  const { data } = await request.post<Comment>(`/posts/${postId}/comments/`, payload)
  return data
}

/** 评论点赞 / 取消点赞（需登录，幂等切换）。 */
export async function likeComment(id: number): Promise<LikeResult> {
  const { data } = await request.post<LikeResult>(`/comments/${id}/like/`)
  return data
}

/** 删除评论（需登录，仅作者或管理员，204 软删）。 */
export async function deleteComment(id: number): Promise<void> {
  await request.delete(`/comments/${id}/`)
}
