import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import { useUserStore } from '@/stores/user'

/** 后端统一错误体：{ message, errors, status }。 */
interface ApiErrorBody {
  message?: string
  errors?: Record<string, unknown> | null
  status?: number
}

/** 可直接展示给用户看的错误。 */
export class ApiError extends Error {
  errors: Record<string, unknown> | null
  status?: number

  constructor(message: string, errors: Record<string, unknown> | null = null, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.errors = errors
    this.status = status
  }
}

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const store = useUserStore()
  if (store.access) {
    config.headers.Authorization = `Bearer ${store.access}`
  }
  return config
})

/** 同一时刻只允许一次刷新，其余请求等待其结果。 */
let refreshing: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const store = useUserStore()
  if (!store.refresh) {
    throw new ApiError('登录已过期，请重新登录', null, 401)
  }
  // 用裸 axios 发刷新请求，避免再次落入本实例的 401 拦截器
  const { data } = await axios.post<{ access: string; refresh?: string }>(
    '/api/v1/auth/refresh/',
    { refresh: store.refresh },
  )
  // 后端开启了 ROTATE_REFRESH_TOKENS：旧的 refresh 已被拉黑，
  // 必须保存返回的新 refresh，否则下次刷新会 401 而被强制登出。
  store.setTokens(data.access, data.refresh ?? store.refresh)
  return data.access
}

function toApiError(error: AxiosError<ApiErrorBody>): ApiError {
  const status = error.response?.status
  const body = error.response?.data

  if (body && typeof body.message === 'string') {
    return new ApiError(body.message, body.errors ?? null, status)
  }
  if (error.code === 'ECONNABORTED') {
    return new ApiError('请求超时，请稍后重试', null, status)
  }
  if (!error.response) {
    return new ApiError('无法连接服务器，请确认后端已启动', null, status)
  }
  return new ApiError('请求失败，请稍后重试', null, status)
}

request.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const status = error.response?.status
    const url = original?.url ?? ''
    const isAuthEndpoint = url.includes('/auth/login/') || url.includes('/auth/refresh/')

    if (status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true
      const store = useUserStore()
      try {
        if (!refreshing) {
          refreshing = refreshAccessToken().finally(() => {
            refreshing = null
          })
        }
        const token = await refreshing
        original.headers.Authorization = `Bearer ${token}`
        return request(original)
      } catch {
        store.clear()
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(new ApiError('登录已过期，请重新登录', null, 401))
      }
    }

    return Promise.reject(toApiError(error))
  },
)

export default request
