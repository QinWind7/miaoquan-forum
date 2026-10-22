/** 与后端 /api/v1 契约一一对应的数据结构。字段名不允许改动。 */

export interface User {
  id: number
  username: string
  nickname: string
  display_name: string
  avatar: string | null
  bio: string
  gender: string
  gender_display: string
  birthday: string | null
  points: number
  level: number
  is_staff: boolean
  date_joined: string
  hide_posts: boolean
  hide_likes: boolean
}

/** GET /users/{id}/ 返回的公开资料：无 email，带隐私开关状态与社交关系。 */
export interface PublicProfile {
  id: number
  username: string
  nickname: string
  display_name: string
  avatar: string | null
  bio: string
  gender: string
  gender_display: string
  level: number
  points: number
  is_staff: boolean
  date_joined: string
  hide_posts: boolean
  hide_likes: boolean
  follower_count: number
  following_count: number
  is_following: boolean
  is_friend: boolean
  has_pending_request: boolean
}

/** 通知类型：点赞/评论为帖子类，其余为社交类。 */
export type NotificationType =
  | 'like'
  | 'comment'
  | 'follow'
  | 'friend_request'
  | 'friend_accept'

/** 站内通知项（GET /notifications/）。 */
export interface NotificationItem {
  id: number
  type: NotificationType
  type_display: string
  actor: UserBrief
  post: number | null
  post_title: string
  comment: number | null
  /** 好友申请类通知关联的申请单 id，铃铛里直接同意/拒绝用 */
  friend_request: number | null
  /** 0 待处理 / 1 已同意 / 2 已拒绝；非好友申请类为 null */
  friend_request_status: number | null
  is_read: boolean
  created_at: string
}

/** GET /social/friends/ 的好友项。 */
export interface FriendItem {
  id: number
  user: UserBrief
  friends_since: string
}

/** GET /social/users/{id}/followers/ 的粉丝项。 */
export interface FollowerItem {
  id: number
  user: UserBrief
  followed_at: string
}

/** 好友申请（收件箱）。 */
export interface FriendRequestItem {
  id: number
  sender: UserBrief
  receiver: UserBrief
  status: 0 | 1 | 2
  status_display: string
  created_at: string
}

/** POST /social/users/{id}/follow/ 的返回。 */
export interface FollowResult {
  following: boolean
  follower_count: number
  following_count: number
}

/** 一条私聊消息。 */
export interface ChatMessage {
  id: number
  sender: UserBrief
  receiver: UserBrief
  content: string
  is_read: boolean
  created_at: string
}

/** 会话列表里的最后一条消息预览。 */
export interface LastChatMessage {
  id: number
  content: string
  is_read: boolean
  /** 这条消息是不是我发的 */
  from_me: boolean
  created_at: string
}

/** GET /chat/conversations/ 的会话项。 */
export interface Conversation {
  partner: UserBrief
  last_message: LastChatMessage
  unread_count: number
  last_at: string
}

/** 帖子/评论里嵌套的作者信息（最小集合）。 */
export interface UserBrief {
  id: number
  username: string
  nickname: string
  display_name: string
  avatar: string | null
  level: number
  is_staff: boolean
}

/** GET /boards/ 直接返回数组，元素结构如下。 */
export interface Board {
  id: number
  name: string
  slug: string
  description: string
  icon: string
  cover: string | null
  color: string
  post_count: number
  sort_order: number
}

/** 帖子里嵌套的分区信息。 */
export interface BoardBrief {
  id: number
  name: string
  slug: string
  color: string
  icon: string
}

export interface Post {
  id: number
  title: string
  summary: string
  cover_image: string | null
  board: BoardBrief
  author: UserBrief
  is_pinned: boolean
  is_essence: boolean
  view_count: number
  like_count: number
  comment_count: number
  created_at: string
  last_comment_at: string | null
  is_liked: boolean
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface AuthResult extends AuthTokens {
  user: User
}

/** DRF 标准分页结构。 */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface LikeResult {
  liked: boolean
  like_count: number
}

/** 图集元素：url 必须以 /media/ 开头，w/h 为原图宽高。 */
export interface PostImage {
  url: string
  w: number
  h: number
}

/** 帖子详情：在列表结构基础上多 content 与 images。 */
export interface PostDetail extends Post {
  content: string
  images: PostImage[]
}

/** 我点赞过的帖子：在列表结构基础上多 liked_at。 */
export interface LikedPost extends Post {
  liked_at: string
}

/**
 * 二级回复：不再嵌套子级（两级封顶）。
 * reply_to_user 只可能出现在回复上。
 */
export interface CommentReply {
  id: number
  post: number
  author: UserBrief
  parent: number | null
  reply_to_user: UserBrief | null
  content: string
  like_count: number
  is_liked: boolean
  is_deleted: boolean
  created_at: string
}

/** 一级评论：内联其全部回复。 */
export interface Comment extends CommentReply {
  replies_count: number
  replies: CommentReply[]
}

export interface CreateCommentPayload {
  content: string
  parent?: number
}

/**
 * 发帖 / 编辑返回体（后端直接序列化 PostWriteSerializer，board 为 slug 字符串）。
 * 提交后前端主要取其中的 id 跳转详情。
 */
export interface PostWriteResult {
  id: number
  title: string
  content: string
  summary: string
  cover_image: string | null
  images: PostImage[]
  board?: string
}

export interface CreatePostPayload {
  board: string
  title: string
  content: string
  summary?: string
  cover_image?: string | null
  images?: PostImage[]
}

/** 编辑时不允许换分区。 */
export type UpdatePostPayload = Omit<CreatePostPayload, 'board'>

/** POST /uploads/image/ 的返回。 */
export interface UploadResult {
  url: string
}

/** GET /themes/ 直接返回数组，不分页。 */
export interface Theme {
  id: number
  name: string
  code: string
  description: string
  preview_image: string | null
  is_dark: boolean
  config: Record<string, unknown>
  sort_order: number
}

/** GET /themes/me/ 我的换肤偏好。 */
export interface MyTheme {
  theme: string | null
  follow_system: boolean
}
