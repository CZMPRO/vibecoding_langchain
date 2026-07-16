<template>
  <div class="layout">
    <AppSidebar
      :sessions="sessions"
      :active-id="activeConversationId"
      @new-chat="onNewChat"
      @select="onSelectSession"
      @rename="onRenameSession"
      @delete="onDeleteSession"
    />

    <div class="main">
      <div class="topbar">
        <div class="title">{{ currentTitle }}</div>
        <div style="display: flex; gap: 8px; align-items: center; color: #64748b; font-size: 13px">
          <span>基于知识库的 RAG 问答</span>
        </div>
      </div>

      <div class="chat-body" ref="bodyRef">
        <div v-if="!messages.length" class="chat-empty">
          <el-icon :size="42" color="#94a3b8"><ChatDotRound /></el-icon>
          <div style="font-size: 16px; color: #334155">👋 开始提问吧</div>
          <div style="font-size: 13px">例如：这款商品支持七天无理由退货吗？有什么规格参数？</div>
        </div>

        <div
          v-for="m in messages"
          :key="m.tempId || m.id"
          class="message-row"
          :class="m.role"
        >
          <div class="bubble" :class="{ 'bubble-md': m.role === 'assistant' }">
            <!-- 等待模型首字时显示「思考中」 -->
            <div v-if="m.role === 'assistant' && m.thinking" class="thinking-indicator" aria-live="polite">
              <span class="thinking-spinner" />
              <span class="thinking-text">思考中</span>
              <span class="thinking-dots" aria-hidden="true">
                <i /><i /><i />
              </span>
            </div>
            <!-- 助手消息：渲染 Markdown，加粗/列表/Emoji 更易读 -->
            <div
              v-else-if="m.role === 'assistant'"
              class="md-body"
              v-html="renderMarkdown(m.content)"
            />
            <div v-else class="plain-body">{{ m.content }}</div>
            <!-- 引用来源：可折叠列表 + 相关度百分比 -->
            <SourceCard
              v-if="m.role === 'assistant' && !m.thinking && m.sources?.length"
              :sources="m.sources"
            />
            <div
              v-if="m.role === 'assistant' && m.id && !String(m.id).startsWith('tmp') && !m.thinking"
              class="feedback-bar"
            >
              <el-button size="small" text @click="onFeedback(m, 1)">👍 有用</el-button>
              <el-button size="small" text @click="onFeedback(m, -1)">👎 没用</el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="composer">
        <div class="composer-box">
          <el-input
            v-model="question"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="请输入关于商品的问题，回车发送（Shift+Enter 换行）"
            :disabled="sending"
            @keydown="onKeydown"
          />
          <div style="display: flex; justify-content: space-between; margin-top: 10px">
            <span style="font-size: 12px; color: #94a3b8">优先知识库；未命中时可常识简答</span>
            <el-button type="primary" :loading="sending" :disabled="!question.trim()" @click="onSend">
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import AppSidebar from '@/components/AppSidebar.vue'
import SourceCard from '@/components/SourceCard.vue'
import {
  askStreamApi,
  createConversationApi,
  deleteConversationApi,
  feedbackApi,
  listConversationsApi,
  listMessagesApi,
  renameConversationApi,
} from '@/api/chat'

// Markdown 渲染：支持加粗、列表、换行；Emoji 原样保留
marked.setOptions({
  gfm: true,
  breaks: true,
})

// 占位符：避免 marked 转义后再还原加粗标签
const STRONG_OPEN = ''
const STRONG_CLOSE = ''
const EM_OPEN = ''
const EM_CLOSE = ''

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 预处理：把 **加粗** / __加粗__ 先换成占位符。
 * 标准 CommonMark 对「中文紧贴 **」侧翼规则很严，
 * 会出现「在**M码**内」原样露出星号的问题。
 */
function preprocessEmphasis(text) {
  let t = String(text)
  // 全角星号先归一成半角，避免模型输出 ＊＊
  t = t.replace(/＊/g, '*').replace(/＿/g, '_')
  // 双星/双下划线加粗（允许内部有中文、括号、标点）
  t = t.replace(/\*\*([^*\n]+?)\*\*/g, `${STRONG_OPEN}$1${STRONG_CLOSE}`)
  t = t.replace(/__([^_\n]+?)__/g, `${STRONG_OPEN}$1${STRONG_CLOSE}`)
  // 单星斜体：仅处理不成对列表冲突较少的场景（两侧非空白）
  t = t.replace(/(^|[\s一-鿿，。；：、！？【】（）])\*([^*\n]+?)\*(?=[\s一-鿿，。；：、！？【】（）]|$)/g, `$1${EM_OPEN}$2${EM_CLOSE}`)
  return t
}

function restoreEmphasis(html) {
  return String(html)
    .replaceAll(STRONG_OPEN, '<strong>')
    .replaceAll(STRONG_CLOSE, '</strong>')
    .replaceAll(EM_OPEN, '<em>')
    .replaceAll(EM_CLOSE, '</em>')
}

function renderMarkdown(text) {
  if (!text) return ''
  try {
    const prepared = preprocessEmphasis(text)
    const html = marked.parse(prepared)
    return restoreEmphasis(html)
  } catch {
    return `<p>${escapeHtml(text)}</p>`
  }
}

const sessions = ref([])
const activeConversationId = ref(null)
const messages = ref([])
const question = ref('')
const sending = ref(false)
const bodyRef = ref()

const currentTitle = computed(() => {
  const s = sessions.value.find((x) => x.id === activeConversationId.value)
  return s?.title || '新会话'
})

async function loadSessions() {
  const { data } = await listConversationsApi({ page: 1, page_size: 100 })
  sessions.value = data.items || []
}

async function loadMessages(conversationId) {
  if (!conversationId) {
    messages.value = []
    return
  }
  const { data } = await listMessagesApi(conversationId, { page: 1, page_size: 200 })
  messages.value = (data.items || []).map((m) => ({
    ...m,
    sources: m.sources || [],
  }))
  await scrollToBottom()
}

async function scrollToBottom() {
  await nextTick()
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  }
}

async function onNewChat() {
  activeConversationId.value = null
  messages.value = []
}

async function onSelectSession(s) {
  activeConversationId.value = s.id
  await loadMessages(s.id)
}

async function onRenameSession(s) {
  const { value } = await ElMessageBox.prompt('请输入新的会话名称', '重命名', {
    inputValue: s.title,
    confirmButtonText: '保存',
    cancelButtonText: '取消',
  })
  if (!value?.trim()) return
  await renameConversationApi(s.id, value.trim())
  ElMessage.success('已重命名')
  await loadSessions()
}

async function onDeleteSession(s) {
  await ElMessageBox.confirm(`确定删除会话「${s.title}」吗？`, '删除确认', { type: 'warning' })
  await deleteConversationApi(s.id)
  if (activeConversationId.value === s.id) {
    activeConversationId.value = null
    messages.value = []
  }
  await loadSessions()
  ElMessage.success('已删除')
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

async function onSend() {
  const q = question.value.trim()
  if (!q || sending.value) return

  sending.value = true
  question.value = ''

  // 本地先插入用户消息和占位助手消息（先显示「思考中」）
  const tempUser = {
    tempId: `tmp-u-${Date.now()}`,
    role: 'user',
    content: q,
    sources: [],
  }
  const tempAssistant = {
    tempId: `tmp-a-${Date.now()}`,
    role: 'assistant',
    content: '',
    sources: [],
    thinking: true,
  }
  messages.value.push(tempUser, tempAssistant)
  await scrollToBottom()

  const stopThinking = () => {
    tempAssistant.thinking = false
  }

  try {
    await askStreamApi(
      {
        conversation_id: activeConversationId.value,
        question: q,
        stream: true,
      },
      {
        onEvent: async (evt) => {
          if (evt.type === 'meta') {
            activeConversationId.value = evt.conversation_id
            // 回填用户消息 id
            tempUser.id = evt.user_message_id
          } else if (evt.type === 'sources') {
            tempAssistant.sources = evt.sources || []
          } else if (evt.type === 'token') {
            // 第一个字到来时结束「思考中」
            if (tempAssistant.thinking) stopThinking()
            tempAssistant.content += evt.content || ''
            await scrollToBottom()
          } else if (evt.type === 'done') {
            stopThinking()
            tempAssistant.content = evt.answer || tempAssistant.content
            tempAssistant.id = evt.assistant_message_id
            if (evt.sources) tempAssistant.sources = evt.sources
            activeConversationId.value = evt.conversation_id || activeConversationId.value
            await loadSessions()
          } else if (evt.type === 'error') {
            stopThinking()
            tempAssistant.content = evt.message || '生成失败'
          }
        },
      },
    )
  } catch (err) {
    stopThinking()
    tempAssistant.content = err.message || '发送失败'
  } finally {
    // 兜底：异常中断时也关掉思考态
    stopThinking()
    sending.value = false
    await scrollToBottom()
  }
}

async function onFeedback(m, rating) {
  try {
    await feedbackApi(m.id, { rating })
    ElMessage.success(rating === 1 ? '已记录：有用' : '已记录：没用')
  } catch {
    // 全局拦截器已提示
  }
}

onMounted(async () => {
  await loadSessions()
  if (sessions.value.length) {
    // 默认不自动打开，保持干净；也可打开最近一条
  }
})
</script>
