import request from './request'
import type { AuthResult, User } from './types'

export interface RegisterPayload {
  username: string
  email?: string
  nickname?: string
  password: string
  password2: string
}

/** 注册：成功直接返回 { access, refresh, user }，无需再跳登录。 */
export async function register(payload: RegisterPayload): Promise<AuthResult> {
  const { data } = await request.post<AuthResult>('/auth/register/', payload)
  return data
}

/** 登录：账号支持用户名或邮箱；rememberMe 会把 refresh token 有效期延长到 30 天。 */
export async function login(
  account: string,
  password: string,
  rememberMe = false,
): Promise<AuthResult> {
  const { data } = await request.post<AuthResult>('/auth/login/', {
    username: account,
    password,
    remember_me: rememberMe,
  })
  return data
}

/** 登出：把 refresh 加入黑名单。 */
export async function logout(refresh: string): Promise<void> {
  await request.post('/auth/logout/', { refresh })
}

/** 当前登录用户资料。 */
export async function me(): Promise<User> {
  const { data } = await request.get<User>('/auth/me/')
  return data
}
