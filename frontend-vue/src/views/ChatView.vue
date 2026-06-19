<template>
  <div class="app-layout">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <!-- 搜索 -->
      <div class="sidebar-search" @click="focusSearch">
        <el-icon><Search /></el-icon>
        <span>搜索...</span>
        <span class="shortcut">Ctrl K</span>
      </div>

      <!-- 用户 -->
      <div class="sidebar-user">
        <div class="user-avatar">🤖</div>
        <span class="user-name">AI 助手</span>
      </div>

      <!-- 功能菜单 -->
      <nav class="sidebar-nav">
        <div class="nav-item active" @click="newChat">
          <el-icon><EditPen /></el-icon>
          <span>新对话</span>
        </div>
        <div class="nav-item" @click="$router.push('/media')">
          <el-icon><Document /></el-icon>
          <span>AI 创作</span>
        </div>
      </nav>

      <!-- 智能体发现 -->
      <div class="sidebar-section">
        <div class="section-header">
          <el-icon><Grid /></el-icon>
          <span>发现智能体</span>
        </div>
      </div>

      <!-- 历史对话 -->
      <div class="sidebar-history">
        <div class="history-label">历史对话</div>
        <div class="history-list">
          <div
            v-for="conv in conversations"
            :key="conv._id"
            class="history-item"
            :class="{ active: currentConvId === conv._id }"
            @click="loadConversation(conv._id)"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span class="history-title">{{ conv.title }}</span>
            <el-icon class="history-delete" @click.stop="removeConversation(conv._id)">
              <Delete />
            </el-icon>
          </div>
          <div v-if="!conversations.length" class="history-empty">暂无历史对话</div>
        </div>
      </div>

      <!-- 底部用户 -->
      <div class="sidebar-footer">
        <div class="footer-user">
          <div class="footer-avatar">U</div>
          <span>管理员</span>
        </div>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="chat-main">
      <!-- 顶部栏 -->
      <header class="chat-header">
        <div class="header-left">
          <el-button text size="small" @click="newChat">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
        <div class="header-center">
          <el-dropdown trigger="click" @command="switchModel">
            <div class="model-selector">
              <span class="model-dot" :style="{ background: modelColor }"></span>
              <span>{{ getProviderLabel(provider) }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="p in providerList" :key="p" :command="p">
                  <span class="model-dot-sm" :style="{ background: getColor(p) }"></span>
                  {{ getProviderLabel(p) }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="header-right">
          <el-button text size="small" @click="showSettings = true">
            <el-icon><MoreFilled /></el-icon>
          </el-button>
        </div>
      </header>

      <!-- 消息区域 -->
      <div class="chat-messages" ref="msgListRef">
        <!-- 空状态 -->
        <div v-if="messages.length === 0 && !loading" class="welcome-screen">
          <div class="welcome-avatar">🤖</div>
          <h2>你好，我是 AI 助手</h2>
          <p>有什么我可以帮你的？</p>
          <div class="welcome-chips">
            <div class="chip" v-for="q in quickQuestions" :key="q" @click="askQuick(q)">
              <span>{{ q }}</span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <!-- 消息 -->
        <template v-for="(msg, i) in messages" :key="i">
          <div class="msg" :class="{ 'msg-user': msg.role === 'user' }">
            <div v-if="msg.role === 'assistant'" class="msg-avatar">
              <span>AI</span>
            </div>
            <div class="msg-content">
              <div v-if="msg.reasoning" class="reasoning-block">
                <div class="reasoning-header" @click="msg._showReasoning = !msg._showReasoning">
                  <span class="reasoning-icon">💡</span>
                  <span>思考过程</span>
                  <span class="reasoning-toggle">{{ msg._showReasoning ? '▾' : '▸' }}</span>
                </div>
                <div v-show="msg._showReasoning" class="reasoning-body">{{ msg.reasoning }}</div>
              </div>
              <div class="msg-text" v-html="renderContent(msg.content)"></div>
              <div v-if="msg.images && msg.images.length" class="msg-images">
                <img v-for="(img, idx) in msg.images" :key="idx" :src="img" class="msg-img" @click="openImgPreview(img)" />
              </div>
              <!-- 消息操作 -->
              <div v-if="msg.role === 'assistant'" class="msg-actions">
                <el-button text size="small" @click="copyMsg(msg.content)"><el-icon><CopyDocument /></el-icon></el-button>
                <el-button text size="small"><el-icon><Top /></el-icon></el-button>
                <el-button text size="small"><el-icon><Bottom /></el-icon></el-button>
              </div>
            </div>
            <div v-if="msg.role === 'user'" class="msg-avatar msg-avatar-user">
              <span>U</span>
            </div>
          </div>

          <!-- 推荐问题 -->
          <div v-if="msg.role === 'assistant' && i === lastAiIndex && suggestions.length && !loading" class="suggest-section">
            <div class="suggest-chips">
              <div class="suggest-chip" v-for="(s, si) in suggestions" :key="si" @click="askQuick(s)">
                <span>{{ s }}</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </template>

        <!-- 任务进度面板 -->
        <div v-if="taskProgress" class="task-progress-panel">
          <div class="task-progress-header">
            <span class="task-icon">📋</span>
            <span>任务执行中</span>
            <span class="task-step-count">{{ taskSteps.length }}/{{ taskProgress.total_steps || '?' }} 步</span>
          </div>
          <div class="task-progress-bar">
            <div class="task-progress-fill" :style="{ width: ((taskSteps.length / (taskProgress.total_steps || 1)) * 100) + '%' }"></div>
          </div>
        </div>

        <!-- 流式输出 -->
        <div v-if="streamingContent || streamingReasoning" class="msg">
          <div class="msg-avatar"><span>AI</span></div>
          <div class="msg-content">
            <div v-if="streamingReasoning" class="reasoning-block">
              <div class="reasoning-header" @click="showReasoning = !showReasoning">
                <span class="reasoning-icon">💡</span>
                <span>思考过程</span>
                <span class="reasoning-toggle">{{ showReasoning ? '▾' : '▸' }}</span>
              </div>
              <div v-show="showReasoning" ref="reasoningRef" class="reasoning-body">{{ streamingReasoning }}</div>
            </div>
            <div v-if="streamingContent" class="msg-text" v-html="renderContent(streamingContent)"></div>
            <span v-if="streamingContent" class="typing-cursor">|</span>
            <span v-if="!streamingContent && streamingReasoning" class="typing-cursor">|</span>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="loading && !streamingContent" class="msg">
          <div class="msg-avatar"><span>AI</span></div>
          <div class="msg-content">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-wrapper">
        <div class="chat-input">
          <!-- 快捷功能栏 -->
          <div class="quick-actions">
            <div class="quick-action" v-for="action in quickActions" :key="action.label" @click="input = action.prompt">
              <span class="qa-icon">{{ action.icon }}</span>
              <span>{{ action.label }}</span>
            </div>
          </div>
          <!-- 图片预览 -->
          <div v-if="attachedImages.length" class="attached-images">
            <div v-for="(img, idx) in attachedImages" :key="idx" class="attached-img-item">
              <img :src="img" />
              <button class="attached-img-remove" @click="removeImage(idx)">✕</button>
            </div>
          </div>
          <!-- 输入框 -->
          <div class="input-box">
            <textarea
              ref="inputRef"
              v-model="input"
              @keydown.enter.exact.prevent="send"
              @paste="handlePaste"
              :disabled="loading"
              placeholder="给我推荐一些关于人工智能的入门书籍"
              rows="1"
            ></textarea>
            <input ref="imageInput" type="file" accept="image/*" multiple style="display:none" @change="handleImageUpload" />
          </div>
          <!-- 底部工具栏 -->
          <div class="input-toolbar">
            <div class="toolbar-left">
              <button class="toolbar-tag" :class="{ active: enableThinking }" @click="enableThinking = !enableThinking">
                <span>💭</span> 深度思考
              </button>
              <button class="toolbar-tag model-tag">
                <span>🧠</span> {{ provider }}
              </button>
            </div>
            <div class="toolbar-right">
              <el-switch v-model="webSearch" size="small" active-text="" inactive-text="" />
              <button class="toolbar-icon-btn" @click="$refs.imageInput.click()">
                <el-icon :size="18"><Picture /></el-icon>
              </button>
              <button class="toolbar-icon-btn" @click="$refs.imageInput.click()">
                <el-icon :size="18"><Plus /></el-icon>
              </button>
            <button v-if="!loading" class="send-btn" :class="{ active: input.trim() || attachedImages.length }" @click="send" :disabled="!input.trim() && !attachedImages.length">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
            <button v-else class="send-btn stop-btn" @click="stopGeneration">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 右侧设置面板 -->
    <transition name="slide">
      <div v-if="showSettings" class="settings-panel">
        <div class="panel-header">
          <span>对话设置</span>
          <el-button text @click="showSettings = false"><el-icon><Close /></el-icon></el-button>
        </div>
        <div class="panel-body">
          <div class="panel-avatar">
            <div class="big-avatar">🤖</div>
            <h3>{{ provider }}</h3>
            <p>AI 智能助手</p>
          </div>
          <div class="panel-menu">
            <div class="menu-item">
              <div class="mi-icon" style="background:#fff3e0;color:#ff9800">
                <el-icon><User /></el-icon>
              </div>
              <span>角色设定</span>
              <el-icon class="mi-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="menu-item">
              <div class="mi-icon" style="background:#e8f5e9;color:#4caf50">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <span>语言</span>
              <el-icon class="mi-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="menu-item">
              <div class="mi-icon" style="background:#e3f2fd;color:#2196f3">
                <el-icon><Share /></el-icon>
              </div>
              <span>公开 · 所有人可对话</span>
              <el-icon class="mi-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="menu-item danger" @click="clearContext">
              <div class="mi-icon" style="background:#fce4ec;color:#f44336">
                <el-icon><Delete /></el-icon>
              </div>
              <span>清除上下文</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Search, EditPen, Document, Grid, ChatDotRound, Delete, Plus,
  ArrowDown, ArrowRight, MoreFilled, CopyDocument, Top, Bottom,
  Close, User, Share, Picture
} from '@element-plus/icons-vue'
import { chatStream, agentChat, getProviders, getSettings, getConversations, getConversation, createConversation, deleteConversation } from '../api'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

const renderContent = (text) => {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch (e) {
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
  }
}

const route = useRoute()

const messages = ref([])
const input = ref('')
const loading = ref(false)
const streamingContent = ref('')
const suggestions = ref([])
const provider = ref('')
const providerList = ref([])
const msgListRef = ref(null)
const inputRef = ref(null)
const conversations = ref([])
const currentConvId = ref(null)
const showSettings = ref(false)
const attachedImages = ref([])

const webSearch = ref(false)

const taskProgress = ref(null)
const taskSteps = ref([])
const currentThought = ref('')
const streamingReasoning = ref('')
const showReasoning = ref(true)
const reasoningRef = ref(null)
const enableThinking = ref(true)
const showModelSwitch = ref(false)
let currentAbortController = null
let aborted = false
const allQuickActions = [
  { icon: '📋', label: '任务', prompt: '帮我制定一个任务计划' },
  { icon: '🎨', label: 'AI 生图', prompt: '帮我生成一张图片' },
  { icon: '📝', label: 'AI 写作', prompt: '帮我写一篇文章' },
  { icon: '📊', label: 'AI PPT', prompt: '帮我制作一份PPT' },
  { icon: '💻', label: 'AI 编程', prompt: '帮我写一段代码' },
  { icon: '🔍', label: '联网搜索', prompt: '帮我搜索一下最新的AI技术趋势' },
  { icon: '📈', label: '数据分析', prompt: '帮我分析这份数据并生成报告' },
  { icon: '🗣️', label: '翻译助手', prompt: '帮我翻译一段英文内容' },
  { icon: '💡', label: '头脑风暴', prompt: '帮我进行头脑风暴' },
  { icon: '📚', label: '读书笔记', prompt: '帮我整理一份读书笔记' },
  { icon: '🎯', label: '目标规划', prompt: '帮我制定一个季度目标规划' },
  { icon: '📧', label: '邮件撰写', prompt: '帮我写一封专业的工作邮件' },
]
const quickActions = ref([])

const refreshQuickActions = () => {
  const shuffled = [...allQuickActions].sort(() => Math.random() - 0.5)
  quickActions.value = shuffled.slice(0, 5)
}

const quickQuestions = [
  '帮我写一份项目周报',
  '解释一下什么是微服务',
  '推荐几本技术书籍',
  '如何优化Python代码性能'
]

const modelColors = { deepseek: '#3b82f6', mimo: '#22c55e', agnes: '#f59e0b', qwen: '#ef4444', glm: '#8b5cf6', openai: '#06b6d4', custom: '#64748b' }
const providerNames = { deepseek: 'DeepSeek', mimo: 'MiMo', agnes: 'Agnes', qwen: '通义千问', glm: '智谱GLM', openai: 'OpenAI', custom: '自定义' }
const modelColor = computed(() => modelColors[provider.value] || '#909399')
const getColor = (name) => modelColors[name] || '#909399'
const getProviderLabel = (name) => providerNames[name] || name

const lastAiIndex = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant') return i
  }
  return -1
})

const systemPrompt = ref('')
const agentName = ref('')

onMounted(async () => {
  refreshQuickActions()
  try {
    const [providersRes, settingsRes] = await Promise.all([getProviders(), getSettings()])
    const registered = providersRes.data.providers?.map(p => p.name) || []
    const settings = settingsRes.data
    const allProviders = ['deepseek', 'mimo', 'agnes', 'qwen', 'glm', 'openai', 'custom']
    const configured = allProviders.filter(name => {
      const key = settings[name + '_key']
      return key && key.length > 0 && !key.startsWith('your-')
    })
    providerList.value = [...new Set([...registered, ...configured])]
    provider.value = providersRes.data.default_provider || configured[0] || 'agnes'
  } catch (e) {
    providerList.value = ['agnes', 'deepseek', 'mimo', 'qwen', 'glm', 'openai', 'custom']
    provider.value = 'agnes'
  }
  await loadConversations()
})

const loadConversations = async () => {
  try {
    const { data } = await getConversations()
    conversations.value = data.conversations || []
  } catch (e) {}
}

const loadConversation = async (convId) => {
  currentConvId.value = convId
  suggestions.value = []
  try {
    const { data } = await getConversation(convId)
    messages.value = data.messages || []
    if (data.provider) provider.value = data.provider
    await nextTick()
    scrollToBottom()
  } catch (e) {}
}

const send = async () => {
  const userMsg = input.value.trim()
  if (!userMsg && !attachedImages.value.length) return
  if (loading.value) return
  input.value = ''

  loading.value = true
  streamingContent.value = ''
  streamingReasoning.value = ''
  suggestions.value = []
  currentThought.value = ''

  // 新对话先创建 conversation
  if (!currentConvId.value) {
    try {
      const { data } = await createConversation(userMsg.slice(0, 30), provider.value)
      currentConvId.value = data.id
      await loadConversations()
    } catch (e) {}
  }

  messages.value.push({ role: 'user', content: userMsg || '(图片)', images: attachedImages.value.length ? [...attachedImages.value] : undefined })
  attachedImages.value = []

  const images = messages.value[messages.value.length - 1]?.images || []

  await nextTick()
  scrollToBottom()

  aborted = false
  let abortCtrl = new AbortController()
  currentAbortController = abortCtrl

  chatStream(currentConvId.value, userMsg, provider.value, systemPrompt.value, images,
    (chunk) => { if (aborted) return; streamingContent.value += chunk; scrollToBottom() },
    (error, sugs) => {
      currentAbortController = null
      if (sugs && sugs.length) suggestions.value = sugs
      if (streamingContent.value) {
        messages.value.push({ role: 'assistant', content: streamingContent.value, reasoning: streamingReasoning.value || '' })
        streamingContent.value = ''
        streamingReasoning.value = ''
      } else if (error && !aborted) {
        messages.value.push({ role: 'assistant', content: `请求失败: ${error}` })
      }
      loading.value = false
      taskProgress.value = null
      taskSteps.value = []
      currentThought.value = ''
      scrollToBottom()
      loadConversations()
    },
    (toolEvent) => {
      if (toolEvent.type === 'reasoning') {
        streamingReasoning.value += toolEvent.data
        nextTick(() => {
          if (reasoningRef.value) reasoningRef.value.scrollTop = reasoningRef.value.scrollHeight
        })
        scrollToBottom()
      } else if (toolEvent.type === 'status') {
        streamingContent.value += `\n\n⏳ ${toolEvent.message}\n`
        scrollToBottom()
              } else if (toolEvent.type === 'intent') {
        const intent = toolEvent.data
        const detail = intent.detail || ''
        if (detail) {
          streamingContent.value += `\n\n🔍 ${detail.replace(/\n/g, '\n   ')}\n`
          scrollToBottom()
        }
      } else if (toolEvent.type === 'thought') {
        currentThought.value = toolEvent.data
        streamingContent.value += `\n\n💭 ${toolEvent.data}\n`
        scrollToBottom()
      } else if (toolEvent.type === 'task_start') {
        taskProgress.value = toolEvent.data
        taskSteps.value = []
        streamingContent.value += `\n\n📋 开始执行任务（共 ${toolEvent.data.total_steps || '?'} 步）\n`
        scrollToBottom()
      } else if (toolEvent.type === 'step_complete') {
        const step = toolEvent.data
        taskSteps.value.push(step)
        streamingContent.value += `\n✅ 步骤完成: ${step.step_id}\n`
        scrollToBottom()
      } else if (toolEvent.type === 'clarification') {
        streamingContent.value += `\n\n❓ ${toolEvent.question}\n`
        scrollToBottom()
      } else if (toolEvent.type === 'result') {
        const r = toolEvent.data
        streamingContent.value += `\n✅ 工具 ${r.tool} 执行完成\n`
        scrollToBottom()
      }
    },
    { web_search: webSearch.value, signal: abortCtrl.signal, enable_thinking: enableThinking.value }
  )
}

const newChat = () => {
  currentConvId.value = null
  messages.value = []
  streamingContent.value = ''
  streamingReasoning.value = ''
  loading.value = false
  taskProgress.value = null
  taskSteps.value = []
  currentThought.value = ''
  refreshQuickActions()
  scrollToBottom()
}

const askQuick = (q) => { input.value = q; send() }
const switchModel = (m) => { provider.value = m }
const focusSearch = () => {}
const scrollToBottom = () => { nextTick(() => { if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight }) }

const removeConversation = async (id) => {
  try {
    await deleteConversation(id)
    conversations.value = conversations.value.filter(c => c._id !== id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
    }
  } catch (e) {}
}

const stopGeneration = () => {
  if (currentAbortController) {
    currentAbortController.abort()
    currentAbortController = null
  }
  aborted = true
}

const handleImageUpload = (event) => {
  const files = event.target.files
  if (!files) return
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue
    const reader = new FileReader()
    reader.onload = (e) => {
      attachedImages.value.push(e.target.result)
    }
    reader.readAsDataURL(file)
  }
  event.target.value = ''
}

const handlePaste = (event) => {
  const items = event.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      const reader = new FileReader()
      reader.onload = (e) => {
        attachedImages.value.push(e.target.result)
      }
      reader.readAsDataURL(file)
      break
    }
  }
}

const removeImage = (idx) => {
  attachedImages.value.splice(idx, 1)
}

const openImgPreview = (src) => {
  window.open(src, '_blank')
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: calc(100vh - 100px);
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

/* ====== 左侧边栏 ====== */
.sidebar {
  width: 260px;
  background: #f7f8fa;
  border-right: 1px solid #eef0f3;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px;
  padding: 10px 14px;
  background: #fff;
  border-radius: 10px;
  font-size: 14px;
  color: #999;
  cursor: pointer;
  border: 1px solid #eee;
}
.sidebar-search .shortcut { margin-left: auto; font-size: 11px; color: #bbb; background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
}
.user-avatar { width: 32px; height: 32px; border-radius: 50%; background: #e8f0fe; display: flex; align-items: center; justify-content: center; font-size: 16px; }
.user-name { font-size: 15px; font-weight: 600; color: #1a1a1a; }

.sidebar-nav { padding: 4px 8px; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 14px;
  color: #444;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}
.nav-item:hover { background: #eef0f3; }
.nav-item.active { background: #e8f0fe; color: #3b82f6; font-weight: 500; }
.nav-badge { position: absolute; right: 12px; background: #f56c6c; color: #fff; font-size: 10px; padding: 1px 6px; border-radius: 8px; }

.sidebar-section { padding: 8px 16px; }
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #888;
  padding: 8px 0;
}

.sidebar-history { flex: 1; overflow-y: auto; padding: 0 8px; }
.history-label { font-size: 12px; color: #bbb; padding: 8px 12px 4px; }
.history-list { display: flex; flex-direction: column; gap: 2px; }
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;
}
.history-item:hover { background: #eef0f3; }
.history-item.active { background: #e8f0fe; color: #3b82f6; }
.history-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-delete { opacity: 0; font-size: 13px; color: #f56c6c; transition: opacity 0.15s; }
.history-item:hover .history-delete { opacity: 1; }
.history-empty { text-align: center; color: #ccc; padding: 20px; font-size: 12px; }

.sidebar-footer { padding: 12px 16px; border-top: 1px solid #eee; }
.footer-user { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #555; }
.footer-avatar { width: 28px; height: 28px; border-radius: 50%; background: #3b82f6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }

/* ====== 主聊天区 ====== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fff;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left, .header-right { display: flex; gap: 4px; }

.model-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: background 0.15s;
}
.model-selector:hover { background: #f5f5f5; }
.model-dot { width: 8px; height: 8px; border-radius: 50%; }
.model-dot-sm { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

/* 消息区 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  scroll-behavior: smooth;
}

.welcome-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.welcome-avatar { font-size: 56px; margin-bottom: 16px; }
.welcome-screen h2 { font-size: 22px; color: #1a1a1a; margin-bottom: 8px; font-weight: 600; }
.welcome-screen p { font-size: 14px; color: #999; margin-bottom: 32px; }
.welcome-chips { display: flex; flex-direction: column; gap: 10px; width: 400px; }
.chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f7f8fa;
  border: 1px solid #eee;
  border-radius: 12px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}
.chip:hover { background: #e8f0fe; border-color: #b3d1ff; color: #3b82f6; }

/* 消息 */
.msg {
  display: flex;
  gap: 12px;
  padding: 8px 24px;
  margin-bottom: 4px;
  animation: fadeIn 0.25s ease;
}
.msg-user { flex-direction: row-reverse; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; } }

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e8f0fe;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.msg-avatar span { font-size: 12px; font-weight: 600; color: #3b82f6; }
.msg-avatar-user { background: #3b82f6; }
.msg-avatar-user span { color: #fff; }

.msg-content { max-width: 70%; min-width: 0; }
.msg-text {
  font-size: 14px;
  line-height: 1.8;
  color: #1a1a1a;
  word-break: break-word;
}
.msg-images {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.msg-img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}
.msg-img:hover { transform: scale(1.02); }
.msg-text :deep(code) { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; font-family: 'Consolas', monospace; font-size: 13px; color: #d56161; }
.msg-text :deep(pre) { background: #1e1e2e; color: #cdd6f4; padding: 14px; border-radius: 8px; overflow-x: auto; margin: 8px 0; font-size: 13px; }
.msg-text :deep(pre code) { background: none; padding: 0; color: inherit; }

.msg-actions {
  display: flex;
  gap: 2px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}
.msg:hover .msg-actions { opacity: 1; }

.typing-cursor { color: #3b82f6; animation: blink 0.8s infinite; font-weight: 300; }

.reasoning-block {
  margin-bottom: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: #f9fafb;
}
.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  user-select: none;
}
.reasoning-header:hover { background: #f3f4f6; }
.reasoning-icon { font-size: 14px; }
.reasoning-toggle { margin-left: auto; font-size: 12px; }
.reasoning-body {
  padding: 0 12px 10px 12px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.7;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
}
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.typing-indicator { display: flex; gap: 4px; padding: 12px 0; }
.typing-indicator span { width: 6px; height: 6px; background: #ccc; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
.typing-indicator span:nth-child(2) { animation-delay: 0.16s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.32s; }
@keyframes bounce { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }

/* 推荐问题 */
.suggest-section { padding: 4px 24px 16px 68px; animation: fadeIn 0.3s ease; }
.suggest-chips { display: flex; flex-direction: column; gap: 8px; }
.suggest-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f7f8fa;
  border: 1px solid #eee;
  border-radius: 10px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}
.suggest-chip:hover { background: #e8f0fe; border-color: #b3d1ff; color: #3b82f6; }

/* 输入区 */
.chat-input-wrapper {
  padding: 12px 24px 20px;
  display: flex;
  justify-content: center;
}
.chat-input {
  width: 100%;
  max-width: 720px;
}

.quick-actions {
  display: flex;
  gap: 8px;
  padding: 0 0 10px;
  overflow-x: auto;
}
.quick-actions::-webkit-scrollbar { display: none; }
.quick-action {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 16px;
  border-radius: 22px;
  background: #f0f4ff;
  color: #1a1a1a;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e0e8ff;
}
.quick-action:hover { background: #dce6ff; border-color: #6b9cff; }
.qa-icon { font-size: 15px; }

.attached-images {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  flex-wrap: wrap;
}
.attached-img-item {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #eee;
}
.attached-img-item img { width: 100%; height: 100%; object-fit: cover; }
.attached-img-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.attached-img-remove:hover { background: rgba(0,0,0,0.7); }

.input-box {
  display: flex;
  align-items: flex-end;
  background: #fff;
  border-radius: 20px;
  padding: 14px 18px;
  border: 1.5px solid #c8cdd5;
  transition: all 0.2s;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.input-box:focus-within {
  border-color: #4b8df8;
  box-shadow: 0 0 0 3px rgba(75,141,248,0.12), 0 2px 12px rgba(0,0,0,0.04);
}
.input-box textarea {
  flex: 1;
  border: none;
  background: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.6;
  max-height: 120px;
  font-family: inherit;
  color: #1a1a1a;
}
.input-box textarea::placeholder { color: #b0b8c4; }

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.toolbar-tag {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  border-radius: 18px;
  border: 1px solid #e2e6eb;
  background: #fff;
  color: #555;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.toolbar-tag:hover { border-color: #4b8df8; color: #4b8df8; }
.toolbar-tag.active { background: #eef4ff; border-color: #4b8df8; color: #4b8df8; }
.model-tag { color: #7c3aed; border-color: #e0dbff; }
.model-tag:hover { background: #f8f5ff; border-color: #7c3aed; }
.toolbar-icon-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: none;
  background: none;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.toolbar-icon-btn:hover { background: #f3f4f6; color: #333; }

.send-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: #e0e4ea;
  color: #b0b8c4;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
.send-btn.active { background: #4b8df8; color: #fff; }
.send-btn.active:hover { background: #3a7ae8; }
.send-btn.stop-btn { background: #ef4444; color: #fff; }
.send-btn.stop-btn:hover { background: #dc2626; }

/* ====== 右侧设置面板 ====== */
.settings-panel {
  width: 320px;
  border-left: 1px solid #eee;
  display: flex;
  flex-direction: column;
  background: #fff;
  flex-shrink: 0;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #eee;
  font-size: 15px;
  font-weight: 600;
}
.panel-body { flex: 1; overflow-y: auto; }
.panel-avatar { text-align: center; padding: 32px 0 24px; }
.big-avatar { width: 64px; height: 64px; border-radius: 50%; background: #e8f0fe; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 12px; }
.panel-avatar h3 { font-size: 18px; color: #1a1a1a; margin-bottom: 4px; }
.panel-avatar p { font-size: 13px; color: #999; }

.panel-menu { padding: 0 16px; }
.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
  color: #333;
  cursor: pointer;
}
.menu-item:hover { color: #3b82f6; }
.mi-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.mi-arrow { margin-left: auto; color: #ccc; }
.menu-item.danger { color: #f44336; }

/* 任务进度面板 */
.task-progress-panel {
  margin: 8px 0;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 12px;
  max-width: 400px;
}
.task-progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 8px;
}
.task-icon { font-size: 16px; }
.task-step-count {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: #0284c7;
}
.task-progress-bar {
  height: 4px;
  background: #bae6fd;
  border-radius: 2px;
  overflow: hidden;
}
.task-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0ea5e9, #06b6d4);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 过渡动画 */
.slide-enter-active, .slide-leave-active { transition: all 0.25s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); opacity: 0; }

@media (max-width: 768px) { .sidebar { display: none; } .settings-panel { position: absolute; right: 0; top: 0; bottom: 0; z-index: 10; } }
</style>
