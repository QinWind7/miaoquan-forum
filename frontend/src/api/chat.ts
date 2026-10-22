import request from './request'
import type { ChatMessage, Conversation } from './types'

/** 我的会话列表（对方 + 最后一条 + 未读数），按最近消息倒序。 */
export async function fetchConversations(): Promise<Conversation[]> {
  const { data } = await request.get<Conversation[]>('/chat/conversations/')
  return data
}

/**
 * 与某人的聊天记录。
 * after 传上次最后一条消息 id 时只返回更新的消息（轮询用），否则返回最近 100 条。
 */
export async function fetchMessages(userId: number, after = 0): Promise<ChatMessage[]> {
  const { data } = await request.get<ChatMessage[]>('/chat/messages/', {
    params: after > 0 ? { user: userId, after } : { user: userId },
  })
  return data
}

/** 发送私聊（仅限好友）。 */
export async function sendMessage(receiver: number, content: string): Promise<ChatMessage> {
  const { data } = await request.post<ChatMessage>('/chat/messages/', { receiver, content })
  return data
}
