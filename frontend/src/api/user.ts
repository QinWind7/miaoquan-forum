import request from './request'
import type { LikedPost, Paginated, Post, PublicProfile, User } from './types'

export interface UserListQuery {
  page?: number
  page_size?: number
}

/** 指定用户的公开资料（不含 email）。 */
export async function fetchUserProfile(id: number): Promise<PublicProfile> {
  const { data } = await request.get<PublicProfile>(`/users/${id}/`)
  return data
}

/** Ta 发表的帖子；对方开启「隐藏发帖」时抛 403。 */
export async function fetchUserPosts(
  id: number,
  params: UserListQuery = {},
): Promise<Paginated<Post>> {
  const { data } = await request.get<Paginated<Post>>(`/users/${id}/posts/`, {
    params: { page_size: 20, ...params },
  })
  return data
}

/** Ta 点赞过的帖子（带 liked_at）；对方开启「隐藏点赞」时抛 403。 */
export async function fetchUserLikes(
  id: number,
  params: UserListQuery = {},
): Promise<Paginated<LikedPost>> {
  const { data } = await request.get<Paginated<LikedPost>>(`/users/${id}/likes/`, {
    params: { page_size: 20, ...params },
  })
  return data
}

/** 修改自己的隐私开关（PATCH /auth/me/，返回最新用户资料）。 */
export async function updateMyPrivacy(payload: {
  hide_posts?: boolean
  hide_likes?: boolean
}): Promise<User> {
  const { data } = await request.patch<User>('/auth/me/', payload)
  return data
}
