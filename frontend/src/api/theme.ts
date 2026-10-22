import request from './request'
import type { MyTheme, Theme } from './types'

/** 全部启用中的皮肤（匿名可读，不分页，直接数组）。 */
export async function fetchThemes(): Promise<Theme[]> {
  const { data } = await request.get<Theme[]>('/themes/')
  return data
}

/** 我的换肤偏好（需登录）。theme 为皮肤 code，未设置时为 null。 */
export async function fetchMyTheme(): Promise<MyTheme> {
  const { data } = await request.get<MyTheme>('/themes/me/')
  return data
}

/** 保存我的换肤偏好（需登录，幂等）；传 null 表示回到默认皮肤。 */
export async function updateMyTheme(theme: string | null): Promise<MyTheme> {
  const { data } = await request.put<MyTheme>('/themes/me/', { theme })
  return data
}
