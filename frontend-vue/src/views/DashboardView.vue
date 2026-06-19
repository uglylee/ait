<template>
  <div class="dashboard">
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <div class="stat-card">
          <div class="stat-icon" :style="{ background: item.color }">{{ item.icon }}</div>
          <div class="stat-info">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <div class="page-card">
          <div class="card-header"><h3>快捷入口</h3></div>
          <div class="card-body">
            <el-row :gutter="16">
              <el-col :span="6" v-for="tool in tools" :key="tool.name">
                <div class="tool-card" @click="$router.push(tool.path)">
                  <div class="tool-icon" :style="{ background: tool.bg }">{{ tool.icon }}</div>
                  <div class="tool-name">{{ tool.name }}</div>
                  <div class="tool-desc">{{ tool.desc }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>

        <div class="page-card" style="margin-top:16px">
          <div class="card-header">
            <h3>最近对话</h3>
            <el-button type="primary" text size="small" @click="$router.push('/chat')">查看更多</el-button>
          </div>
          <div class="card-body">
            <el-table :data="recentChats" stripe style="width:100%" v-loading="loading">
              <el-table-column prop="time" label="时间" width="160" />
              <el-table-column prop="model" label="模型" width="120" />
              <el-table-column prop="message" label="内容" show-overflow-tooltip />
            </el-table>
            <div v-if="!loading && recentChats.length === 0" style="text-align:center;padding:20px;color:#909399">暂无对话记录</div>
          </div>
        </div>
      </el-col>

      <el-col :span="8">
        <div class="page-card">
          <div class="card-header"><h3>系统状态</h3></div>
          <div class="card-body">
            <div class="status-list">
              <div class="status-item" v-for="s in systemStatus" :key="s.name">
                <div class="status-left">
                  <div class="status-dot" :style="{ background: s.ok ? '#67c23a' : '#f56c6c' }"></div>
                  <span>{{ s.name }}</span>
                </div>
                <el-tag :type="s.ok ? 'success' : 'danger'" size="small">{{ s.ok ? '正常' : '异常' }}</el-tag>
              </div>
            </div>
          </div>
        </div>

        <div class="page-card" style="margin-top:16px">
          <div class="card-header"><h3>可用模型</h3></div>
          <div class="card-body">
            <div class="model-list">
              <div class="model-item" v-for="m in models" :key="m.name">
                <div class="model-dot" :style="{ background: m.color }"></div>
                <div class="model-info">
                  <div class="model-name">{{ m.name }}</div>
                  <div class="model-desc">{{ m.desc }}</div>
                </div>
                <el-tag size="small" :type="m.available ? 'success' : 'info'">{{ m.available ? '可用' : '未配置' }}</el-tag>
              </div>
            </div>
          </div>
        </div>

        <div class="page-card" style="margin-top:16px">
          <div class="card-header"><h3>今日使用量</h3></div>
          <div class="card-body">
            <div class="usage-bar">
              <div class="usage-item" v-for="u in usage" :key="u.name">
                <div class="usage-label">
                  <span>{{ u.name }}</span>
                  <span>{{ u.value }} 次</span>
                </div>
                <el-progress :percentage="u.pct" :stroke-width="8" />
              </div>
              <div v-if="usage.length === 0" style="text-align:center;padding:12px;color:#909399;font-size:13px">今日暂无使用</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
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

<style scoped>
.stat-row { margin-bottom: 16px; }
.stat-card {
  background: #fff; border-radius: 8px; padding: 20px;
  display: flex; align-items: center; gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 24px;
}
.stat-value { font-size: 24px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }

.status-list { display: flex; flex-direction: column; gap: 12px; }
.status-item { display: flex; justify-content: space-between; align-items: center; }
.status-left { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #303133; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }

.model-list { display: flex; flex-direction: column; gap: 12px; }
.model-item { display: flex; align-items: center; gap: 10px; }
.model-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.model-info { flex: 1; }
.model-name { font-size: 14px; font-weight: 500; color: #303133; }
.model-desc { font-size: 12px; color: #909399; }

.usage-bar { display: flex; flex-direction: column; gap: 16px; }
.usage-label { display: flex; justify-content: space-between; font-size: 13px; color: #606266; margin-bottom: 4px; }
</style>
