<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <div class="stat-card">
          <div class="stat-icon" :style="{ background: item.color }">
            {{ item.icon }}
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 快捷入口 -->
      <el-col :span="16">
        <div class="page-card">
          <div class="card-header">
            <h3>快捷入口</h3>
          </div>
          <div class="card-body">
            <el-row :gutter="16">
              <el-col :span="6" v-for="tool in tools" :key="tool.name">
                <div class="tool-card" @click="$router.push(tool.path)">
                  <div class="tool-icon" :style="{ background: tool.bg }">
                    {{ tool.icon }}
                  </div>
                  <div class="tool-name">{{ tool.name }}</div>
                  <div class="tool-desc">{{ tool.desc }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 最近对话 -->
        <div class="page-card" style="margin-top:16px">
          <div class="card-header">
            <h3>最近对话</h3>
            <el-button type="primary" text size="small" @click="$router.push('/chat')">查看更多</el-button>
          </div>
          <div class="card-body">
            <el-table :data="recentChats" stripe style="width:100%">
              <el-table-column prop="time" label="时间" width="160" />
              <el-table-column prop="model" label="模型" width="120" />
              <el-table-column prop="message" label="内容" show-overflow-tooltip />
              <el-table-column prop="tokens" label="Token" width="80" align="right" />
            </el-table>
          </div>
        </div>
      </el-col>

      <!-- 右侧 -->
      <el-col :span="8">
        <!-- 系统状态 -->
        <div class="page-card">
          <div class="card-header">
            <h3>系统状态</h3>
          </div>
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

        <!-- AI 模型 -->
        <div class="page-card" style="margin-top:16px">
          <div class="card-header">
            <h3>可用模型</h3>
          </div>
          <div class="card-body">
            <div class="model-list">
              <div class="model-item" v-for="m in models" :key="m.name">
                <div class="model-dot" :style="{ background: m.color }"></div>
                <div class="model-info">
                  <div class="model-name">{{ m.name }}</div>
                  <div class="model-desc">{{ m.desc }}</div>
                </div>
                <el-tag size="small" :type="m.available ? 'success' : 'info'">
                  {{ m.available ? '可用' : '未配置' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 使用量趋势 -->
        <div class="page-card" style="margin-top:16px">
          <div class="card-header">
            <h3>今日使用量</h3>
          </div>
          <div class="card-body">
            <div class="usage-bar">
              <div class="usage-item" v-for="u in usage" :key="u.name">
                <div class="usage-label">
                  <span>{{ u.name }}</span>
                  <span>{{ u.value }} 次</span>
                </div>
                <el-progress :percentage="u.pct" :stroke-width="8" />
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { healthCheck, getProviders } from '../api'

const stats = ref([
  { icon: '💬', label: '今日对话', value: '128', color: '#ecf5ff' },
  { icon: '✍️', label: '生成文章', value: '23', color: '#f0f9eb' },
  { icon: '📊', label: '推荐请求', value: '1,024', color: '#fdf6ec' },
  { icon: '📷', label: 'OCR 识别', value: '56', color: '#fef0f0' },
])

const tools = ref([
  { icon: '💬', name: 'AI 对话', desc: '多模型智能对话', path: '/chat', bg: '#ecf5ff' },
  { icon: '🎨', name: 'AI 创作', desc: '图像视频与文章生成', path: '/media', bg: '#f0f9eb' },
  { icon: '📊', name: '智能推荐', desc: '个性化推荐引擎', path: '/recommend', bg: '#fdf6ec' },
  { icon: '📷', name: 'OCR 识别', desc: '图片文字提取', path: '/ocr', bg: '#fef0f0' },
  { icon: '📚', name: '知识库', desc: '文档管理与检索', path: '/knowledge', bg: '#f4f4f5' },
  { icon: '⚡', name: '工作流', desc: 'AI 自动化流程', path: '/workflow', bg: '#ecf5ff' },
])

const recentChats = ref([
  { time: '2026-06-17 22:05', model: 'DeepSeek', message: '如何用Python实现快速排序？', tokens: 156 },
  { time: '2026-06-17 21:58', model: 'MiMo', message: '帮我分析一下这个数据集的特征', tokens: 234 },
  { time: '2026-06-17 21:30', model: 'DeepSeek', message: '写一个React组件实现拖拽排序', tokens: 512 },
  { time: '2026-06-17 20:15', model: '通义千问', message: '解释一下什么是微服务架构', tokens: 189 },
])

const systemStatus = ref([
  { name: '后端 API', ok: true },
  { name: 'PostgreSQL', ok: true },
  { name: 'Redis', ok: true },
  { name: 'MongoDB', ok: true },
  { name: 'DeepSeek API', ok: false },
])

const models = ref([
  { name: 'DeepSeek', desc: 'deepseek-chat', color: '#409eff', available: false },
  { name: 'MiMo', desc: 'mimo-auto', color: '#67c23a', available: false },
  { name: 'Agnes', desc: 'agnes-2.0-flash', color: '#e6a23c', available: false },
  { name: '通义千问', desc: 'qwen-turbo', color: '#f56c6c', available: false },
  { name: '智谱GLM', desc: 'glm-4-flash', color: '#909399', available: false },
])

const usage = ref([
  { name: 'AI 对话', value: 128, pct: 64 },
  { name: 'AI 写作', value: 23, pct: 23 },
  { name: 'OCR 识别', value: 56, pct: 28 },
])

onMounted(async () => {
  try {
    const { data } = await getProviders()
    if (data.providers) {
      models.value = models.value.map(m => ({
        ...m,
        available: data.providers.some(p => p.name === m.name.toLowerCase().replace(/通义千问/, 'qwen').replace(/智谱GLM/, 'glm'))
      }))
    }
  } catch (e) {}
})
</script>

<style scoped>
.stat-row { margin-bottom: 16px; }
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
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
