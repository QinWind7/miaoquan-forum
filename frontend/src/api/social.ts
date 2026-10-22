import request from './request'
import type {
  FollowerItem,
  FollowResult,
  FriendItem,
  FriendRequestItem,
  Paginated,
} from './types'

export interface SocialListQuery {
  page?: number
  page_size?: number
}

/** 关注 / 取关（同一个接口切换），返回最新关注状态与双方计数。 */
export async function toggleFollow(userId: number): Promise<FollowResult> {
  const { data } = await request.post<FollowResult>(`/social/users/${userId}/follow/`)
  return data
}

/** 某人的粉丝列表（公开）。 */
export async function fetchFollowers(
  userId: number,
  params: SocialListQuery = {},
): Promise<Paginated<FollowerItem>> {
  const { data } = await request.get<Paginated<FollowerItem>>(
    `/social/users/${userId}/followers/`,
    { params: { page_size: 20, ...params } },
  )
  return data
}

/** 我的好友列表。 */
export async function fetchFriends(
  params: SocialListQuery = {},
): Promise<Paginated<FriendItem>> {
  const { data } = await request.get<Paginated<FriendItem>>('/social/friends/', {
    params: { page_size: 20, ...params },
  })
  return data
}

/** 发送好友申请；对方此前已申请过我时，后端会自动互相通过。 */
export async function sendFriendRequest(receiverId: number): Promise<FriendRequestItem> {
  const { data } = await request.post<FriendRequestItem>('/social/friend-requests/', {
    receiver: receiverId,
  })
  return data
}

/** 我收到的好友申请（?status=0 只看待处理）。 */
export async function fetchFriendRequests(
  params: { status?: 0 | 1 | 2 } & SocialListQuery = {},
): Promise<Paginated<FriendRequestItem>> {
  const { data } = await request.get<Paginated<FriendRequestItem>>(
    '/social/friend-requests/',
    { params: { page_size: 20, ...params } },
  )
  return data
}

export async function acceptFriendRequest(id: number): Promise<FriendRequestItem> {
  const { data } = await request.post<FriendRequestItem>(
    `/social/friend-requests/${id}/accept/`,
  )
  return data
}

export async function rejectFriendRequest(id: number): Promise<FriendRequestItem> {
  const { data } = await request.post<FriendRequestItem>(
    `/social/friend-requests/${id}/reject/`,
  )
  return data
}
