import http from './http'
import { useUserStore } from '@/stores/user'

export function listConversationsApi(params) {
  return http.get('/chat/conversations', { params })
}

export function createConversationApi(data) {
  return http.post('/chat/conversations', data || {})
}

export function renameConversationApi(id, title) {
  return http.patch(`/chat/conversations/${id}`, { title })
}

export function deleteConversationApi(id) {
  return http.delete(`/chat/conversations/${id}`)
}

export function listMessagesApi(id, params) {
  return http.get(`/chat/conversations/${id}/messages`, { params })
}

export function feedbackApi(messageId, data) {
  return http.post(`/chat/messages/${messageId}/feedback`, data)
}

/**
 * SSE 流式问答：通过 fetch 读取事件流。
 * onEvent(eventObj) 处理每个 JSON 事件。
 */
export async function askStreamApi(payload, { onEvent, signal } = {}) {
  const userStore = useUserStore()
  const resp = await fetch('/api/chat/ask/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${userStore.token || ''}`,
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!resp.ok) {
    let detail = '问答请求失败'
    try {
      const data = await resp.json()
      detail = data.detail || detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE 以空行分隔事件
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const lines = part.split('\n')
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const raw = line.slice(5).trim()
          if (!raw) continue
          try {
            const evt = JSON.parse(raw)
            onEvent && onEvent(evt)
          } catch {
            // ignore bad chunk
          }
        }
      }
    }
  }
}
