<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Stats Row -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
      <div v-for="item in stats" :key="item.label" class="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" :style="{ background: item.color }">{{ item.icon }}</div>
        <div>
          <div class="text-2xl font-bold text-gray-800">{{ item.value }}</div>
          <div class="text-xs text-gray-400 mt-0.5">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- Left Column -->
      <div class="lg:col-span-3 flex flex-col gap-4">
        <!-- Quick Tools -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-800">快捷入口</h3>
          </div>
          <div class="p-5">
            <div class="grid grid-cols-3 gap-4">
              <div v-for="tool in tools" :key="tool.name"
                class="text-center p-4 rounded-xl cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
                @click="$router.push(tool.path)"
              >
                <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mx-auto mb-2" :style="{ background: tool.bg }">{{ tool.icon }}</div>
                <div class="text-sm font-medium text-gray-700">{{ tool.name }}</div>
                <div class="text-xs text-gray-400 mt-0.5">{{ tool.desc }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Chats -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-800">最近对话</h3>
            <el-button type="primary" text size="small" @click="$router.push('/chat')">查看更多</el-button>
          </div>
          <div class="p-5">
            <el-table :data="recentChats" stripe style="width:100%" v-loading="loading">
              <el-table-column prop="time" label="时间" width="160" />
              <el-table-column prop="model" label="模型" width="120" />
              <el-table-column prop="message" label="内容" show-overflow-tooltip />
            </el-table>
            <div v-if="!loading && recentChats.length === 0" class="text-center py-5 text-gray-400 text-sm">暂无对话记录</div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="lg:col-span-2 flex flex-col gap-4">
        <!-- System Status -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-800">系统状态</h3>
          </div>
          <div class="p-5 flex flex-col gap-3">
            <div class="flex justify-between items-center" v-for="s in systemStatus" :key="s.name">
              <div class="flex items-center gap-2 text-sm text-gray-700">
                <div class="w-2 h-2 rounded-full" :style="{ background: s.ok ? '#67c23a' : '#f56c6c' }"></div>
                <span>{{ s.name }}</span>
              </div>
              <el-tag :type="s.ok ? 'success' : 'danger'" size="small">{{ s.ok ? '正常' : '异常' }}</el-tag>
            </div>
          </div>
        </div>

        <!-- Models -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-800">可用模型</h3>
          </div>
          <div class="p-5 flex flex-col gap-3">
            <div class="flex items-center gap-3" v-for="m in models" :key="m.name">
              <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ background: m.color }"></div>
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-700">{{ m.name }}</div>
                <div class="text-xs text-gray-400">{{ m.desc }}</div>
              </div>
              <el-tag size="small" :type="m.available ? 'success' : 'info'">{{ m.available ? '可用' : '未配置' }}</el-tag>
            </div>
          </div>
        </div>

        <!-- Usage -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-800">今日使用量</h3>
          </div>
          <div class="p-5 flex flex-col gap-4">
            <div v-for="u in usage" :key="u.name">
              <div class="flex justify-between text-sm text-gray-600 mb-1">
                <span>{{ u.name }}</span>
                <span>{{ u.value }} 次</span>
              </div>
              <el-progress :percentage="u.pct" :stroke-width="8" />
            </div>
            <div v-if="usage.length === 0" class="text-center py-3 text-gray-400 text-xs">今日暂无使用</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '../api'

const loading = ref(true)

const stats = ref([
  { icon: '💬', label: '今日对话', value: 0, color: '#ecf5ff' },
  { icon: '⚡', label: '工作流', value: 0, color: '#f0f9eb', key: 'workflows' },
  { icon: '📋', label: '对话总数', value: 0, color: '#fdf6ec' },
  { icon: '🤖', label: '智能体', value: 0, color: '#fef0f0' },
])

const tools = ref([
  { icon: '💬', name: 'AI 对话', desc: '多模型智能对话', path: '/chat', bg: '#ecf5ff' },
  { icon: '🎨', name: 'AI 创作', desc: '图像视频与文章生成', path: '/media', bg: '#f0f9eb' },
  { icon: '📊', name: '智能推荐', desc: '个性化推荐引擎', path: '/recommend', bg: '#fdf6ec' },
  { icon: '📷', name: 'OCR 识别', desc: '图片文字提取', path: '/ocr', bg: '#fef0f0' },
  { icon: '📚', name: '知识库', desc: '文档管理与检索', path: '/knowledge', bg: '#f4f4f5' },
  { icon: '⚡', name: '工作流', desc: 'AI 自动化流程', path: '/workflow', bg: '#ecf5ff' },
])

const recentChats = ref([])
const systemStatus = ref([])
const models = ref([])
const usage = ref([])

const modelNameMap = {
  deepseek: { name: 'DeepSeek', desc: 'deepseek-chat', color: '#409eff' },
  mimo: { name: 'MiMo', desc: 'mimo-auto', color: '#67c23a' },
  openai: { name: 'OpenAI', desc: 'gpt-3.5/4', color: '#10a37f' },
  qwen: { name: '通义千问', desc: 'qwen-turbo', color: '#f56c6c' },
  glm: { name: '智谱GLM', desc: 'glm-4-flash', color: '#909399' },
  agnes: { name: 'Agnes', desc: 'agnes-2.0-flash', color: '#e6a23c' },
}

onMounted(async () => {
  try {
    const { data } = await getDashboard()
    const s = data.stats || {}
    stats.value[0].value = s.conversations_today || 0
    stats.value[1].value = s.workflows_total || 0
    stats.value[2].value = s.conversations_total || 0
    stats.value[3].value = s.agents_total || 0

    recentChats.value = data.recent_chats || []
    systemStatus.value = data.system_status || []

    const providers = data.providers || []
    models.value = Object.entries(modelNameMap).map(([key, info]) => ({
      ...info,
      available: providers.find(p => p.name === key)?.available || false
    }))

    usage.value = data.usage || []
  } catch (e) {
    console.error('Dashboard load failed:', e)
  } finally {
    loading.value = false
  }
})
</script>
