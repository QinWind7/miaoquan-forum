import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/** 相对时间：如「3 小时前」。 */
export function fromNow(value: string | null | undefined): string {
  if (!value) return ''
  return dayjs(value).fromNow()
}

/** 数字压缩：12345 → 1.2w，1234 → 1.2k。 */
export function compactCount(value: number | null | undefined): string {
  const n = value ?? 0
  if (n >= 10000) return `${(n / 10000).toFixed(1).replace(/\.0$/, '')}w`
  if (n >= 1000) return `${(n / 1000).toFixed(1).replace(/\.0$/, '')}k`
  return String(n)
}
