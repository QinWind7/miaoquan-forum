import request from './request'
import type { Board } from './types'

/**
 * 分区列表：该接口【不分页】，直接返回数组。
 * 元素形如 { id, name, slug, description, icon, cover, color, post_count, sort_order }。
 */
export async function fetchBoards(): Promise<Board[]> {
  const { data } = await request.get<Board[]>('/boards/')
  return data
}

/** 分区详情：按 slug 查询。 */
export async function fetchBoard(slug: string): Promise<Board> {
  const { data } = await request.get<Board>(`/boards/${slug}/`)
  return data
}
