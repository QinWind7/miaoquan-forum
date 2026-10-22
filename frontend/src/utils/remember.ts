/**
 * 「记住我」的本地存储。
 *
 * 注意：这里做的是 base64 + 固定密钥 XOR 的**混淆**，不是真正的加密 ——
 * 密钥打包在前端代码里，任何人打开控制台都能还原。它的作用只是让密码
 * 不以明文躺在 localStorage 里，别把它当安全措施使用。
 * 真正的安全边界仍然是 JWT 与后端的密码哈希。
 */

const ACCOUNT_KEY = 'miao_remember_account'
const PASSWORD_KEY = 'miao_remember_pwd'
const XOR_KEY = 'miaoquan-paw-2026'

function xor(text: string): string {
  let out = ''
  for (let i = 0; i < text.length; i += 1) {
    out += String.fromCharCode(text.charCodeAt(i) ^ XOR_KEY.charCodeAt(i % XOR_KEY.length))
  }
  return out
}

function encode(value: string): string {
  // 先 encodeURIComponent 转成纯 ASCII，保证 btoa 不会因中文/emoji 抛错
  return btoa(encodeURIComponent(xor(value)))
}

function decode(value: string): string {
  try {
    return xor(decodeURIComponent(atob(value)))
  } catch {
    return ''
  }
}

export interface RememberedAccount {
  account: string
  password: string
}

export function saveRemembered(account: string, password: string): void {
  try {
    localStorage.setItem(ACCOUNT_KEY, account)
    localStorage.setItem(PASSWORD_KEY, encode(password))
  } catch {
    // 隐私模式 / 存储被禁用时静默失败，不影响登录本身
  }
}

export function loadRemembered(): RememberedAccount | null {
  try {
    const account = localStorage.getItem(ACCOUNT_KEY)
    const encoded = localStorage.getItem(PASSWORD_KEY)
    if (!account || !encoded) return null
    return { account, password: decode(encoded) }
  } catch {
    return null
  }
}

export function clearRemembered(): void {
  try {
    localStorage.removeItem(ACCOUNT_KEY)
    localStorage.removeItem(PASSWORD_KEY)
  } catch {
    // 忽略
  }
}
