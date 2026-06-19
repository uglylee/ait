<template>
  <div class="h-full flex flex-col gap-4">
    <!-- 输入卡片 -->
    <div class="glass-card p-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">AI 写作</h1>
      <p class="text-gray-500 mb-6">输入主题，一键生成专业文章</p>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">文章主题</label>
          <input
            v-model="topic"
            class="modern-input"
            placeholder="例如：人工智能在医疗领域的应用"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">写作风格</label>
            <el-select v-model="style" class="w-full">
              <el-option label="专业分析" value="专业分析" />
              <el-option label="科普文章" value="科普文章" />
              <el-option label="新闻报道" value="新闻报道" />
              <el-option label="教程风格" value="教程风格" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">文章长度</label>
            <el-select v-model="length" class="w-full">
              <el-option label="短篇 (500字)" value="short" />
              <el-option label="中篇 (1000字)" value="medium" />
              <el-option label="长篇 (2000字)" value="long" />
            </el-select>
          </div>
        </div>

        <button
          @click="generate"
          class="gradient-btn w-full py-3"
          :disabled="loading || !topic.trim()"
        >
          <span v-if="!loading">✨ 开始生成</span>
          <span v-else class="flex items-center justify-center gap-2">
            <el-icon class="animate-spin"><Loading /></el-icon>
            生成中...
          </span>
        </button>
      </div>
    </div>

    <!-- 结果卡片 -->
    <div v-if="result" class="glass-card p-6 flex-1 overflow-hidden flex flex-col">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-gray-800">生成结果</h2>
        <div class="flex gap-2">
          <el-tag type="info">{{ result.word_count }} 字</el-tag>
          <el-tag type="success">{{ result.reading_time }}</el-tag>
        </div>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div class="prose max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">
          {{ result.content }}
        </div>
      </div>
      <div class="mt-4 pt-4 border-t border-gray-100 flex justify-end gap-2">
        <el-button @click="copyContent">
          <el-icon><CopyDocument /></el-icon>
          复制
        </el-button>
        <el-button type="primary" @click="result = null">
          <el-icon><RefreshRight /></el-icon>
          重新生成
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Loading, CopyDocument, RefreshRight } from '@element-plus/icons-vue'
import { generateContent } from '../api'
import { ElMessage } from 'element-plus'

const topic = ref('')
const style = ref('专业分析')
const length = ref('medium')
const loading = ref(false)
const result = ref(null)

const generate = async () => {
  if (!topic.value.trim()) return

  loading.value = true
  try {
    const { data } = await generateContent(topic.value, style.value, length.value)
    result.value = data
  } catch (error) {
    ElMessage.error('生成失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const copyContent = () => {
  if (result.value) {
    navigator.clipboard.writeText(result.value.content)
    ElMessage.success('已复制到剪贴板')
  }
}
</script>
