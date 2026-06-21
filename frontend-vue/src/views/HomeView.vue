<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Welcome -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-800">AIT 智能工作台</h1>
      <p class="text-sm text-gray-400 mt-1">AI 应用通用框架，选择功能开始使用</p>
    </div>

    <!-- Feature Cards Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <div
        v-for="card in cards"
        :key="card.route"
        class="bg-white rounded-xl p-5 shadow-sm border border-gray-100 cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-1 group"
        @click="$router.push(card.route)"
      >
        <div
          class="w-11 h-11 rounded-xl flex items-center justify-center text-xl mb-3 transition-transform duration-200 group-hover:scale-110"
          :style="{ background: card.bg }"
        >
          {{ card.icon }}
        </div>
        <h3 class="text-sm font-semibold text-gray-800 mb-0.5">{{ card.title }}</h3>
        <p class="text-xs text-gray-400 leading-relaxed">{{ card.desc }}</p>
      </div>
    </div>

    <!-- Stats -->
    <div class="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
        <div class="text-2xl font-bold text-indigo-500">{{ stats.conversations_total || 0 }}</div>
        <div class="text-xs text-gray-400 mt-1">总对话数</div>
      </div>
      <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
        <div class="text-2xl font-bold text-violet-500">{{ stats.workflows_total || 0 }}</div>
        <div class="text-xs text-gray-400 mt-1">工作流数</div>
      </div>
      <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
        <div class="text-2xl font-bold text-cyan-500">{{ stats.agents_total || 0 }}</div>
        <div class="text-xs text-gray-400 mt-1">智能体数</div>
      </div>
      <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
        <div class="text-2xl font-bold text-green-500">{{ stats.conversations_today || 0 }}</div>
        <div class="text-xs text-gray-400 mt-1">今日对话</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '../api/index'

const stats = ref({})

const cards = [
  { icon: '💻', title: '工作台', desc: '数据概览与快捷操作', route: '/dashboard', bg: '#ecf5ff' },
  { icon: '💬', title: 'AI 对话', desc: '多模型智能对话', route: '/chat', bg: '#f0f9eb' },
  { icon: '🖥️', title: '代码生成', desc: 'AI 生成可运行代码', route: '/codegen', bg: '#f4f0ff' },
  { icon: '📊', title: '智能推荐', desc: '个性化内容推荐', route: '/recommend', bg: '#fff7e6' },
  { icon: '📷', title: 'OCR 识别', desc: '图片文字智能识别', route: '/ocr', bg: '#fff0f0' },
  { icon: '🎬', title: 'AI 创作', desc: '图像视频内容创作', route: '/media', bg: '#e6fffb' },
  { icon: '📚', title: '知识库', desc: 'RAG 检索增强生成', route: '/knowledge', bg: '#eef0ff' },
  { icon: '🤖', title: '发现智能体', desc: '浏览和创建智能体', route: '/discover', bg: '#fff0f6' },
  { icon: '⚡', title: '工作流', desc: '可视化流程编排', route: '/workflow', bg: '#e6fffe' },
  { icon: '⚙️', title: '系统设置', desc: 'LLM 配置与管理', route: '/settings', bg: '#f5f5f5' },
]

onMounted(async () => {
  try {
    const res = await getDashboard()
    stats.value = res.data?.stats || {}
  } catch {}
})
</script>
