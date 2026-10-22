import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

/** 关闭原生 HTML，避免把未消毒的标签直接透传给 v-html。 */
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

/**
 * 渲染 Markdown 后再用 DOMPurify 消毒，返回值可直接用于 v-html。
 * 正文里的 /media/... 图片路径会被 markdown-it 原样保留，能正常显示。
 */
export function renderMarkdown(source: string | null | undefined): string {
  const raw = md.render(source ?? '')
  return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
}
