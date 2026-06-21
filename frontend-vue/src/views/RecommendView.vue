<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 mb-4">
      <div class="px-5 py-4 border-b border-gray-100">
        <h3 class="text-base font-semibold text-gray-800">智能推荐</h3>
      </div>
      <div class="p-5">
        <el-form :inline="true" :model="form">
          <el-form-item label="用户 ID">
            <el-input v-model="form.userId" placeholder="输入用户ID" />
          </el-form-item>
          <el-form-item label="推荐数量">
            <el-select v-model="form.topK" style="width:100px">
              <el-option :label="3" :value="3" />
              <el-option :label="5" :value="5" />
              <el-option :label="10" :value="10" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="getRec">获取推荐</el-button>
          </el-form-item>
        </el-form>
        <div v-if="!loading && searched && !list.length" class="mt-3 text-sm text-gray-400">
          暂无推荐内容，请先在 AI 对话中发送一些消息
        </div>
      </div>
    </div>

    <div v-if="list.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="(item, i) in list"
        :key="i"
        class="bg-white rounded-xl p-5 shadow-sm border border-gray-100 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
      >
        <div class="flex justify-between items-center mb-3">
          <div class="w-11 h-11 rounded-xl flex items-center justify-center text-xl" :style="{ background: colors[i % 5] }">{{ icons[item.type] || '📌' }}</div>
          <div v-if="scores[i]" class="text-2xl font-bold text-indigo-500">{{ (scores[i] * 100).toFixed(0) }}%</div>
        </div>
        <div class="text-sm font-semibold text-gray-800 mb-1">{{ item.title }}</div>
        <div class="text-xs text-gray-400 mb-2">类型：{{ item.type }}</div>
        <el-button type="primary" text size="small" @click="showDetail(item)">查看详情 →</el-button>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="推荐详情" width="600px">
      <div v-if="detailItem">
        <h4 class="text-sm font-semibold text-gray-800 mb-3">用户对话</h4>
        <div class="bg-gray-50 p-3 rounded-lg text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{{ detailItem.full_text }}</div>

        <div v-if="detailItem.related && detailItem.related.length" class="mt-4">
          <h4 class="text-sm font-semibold text-gray-800 mb-3">相关知识库内容</h4>
          <div v-for="(r, i) in detailItem.related" :key="i" class="bg-green-50 p-3 rounded-lg mb-2">
            <div class="text-xs text-green-600 mb-1">相似度 {{ (1 - r.score) * 100 }}%</div>
            <div class="text-sm text-gray-700 leading-relaxed">{{ r.content }}</div>
          </div>
        </div>

        <div v-if="!detailItem.related || !detailItem.related.length" class="mt-4 text-sm text-gray-400">
          暂无相关知识库内容
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getRecommendations } from '../api'
import { ElMessage } from 'element-plus'

const form = ref({ userId: 'default_user', topK: 5 })
const loading = ref(false)
const searched = ref(false)
const list = ref([])
const scores = ref([])
const colors = ['#ecf5ff', '#f0f9eb', '#fdf6ec', '#fef0f0', '#f4f4f5']
const icons = { content: '📝', product: '🛒', article: '📰', video: '🎬', service: '🔧' }
const dialogVisible = ref(false)
const detailItem = ref(null)

const showDetail = (item) => { detailItem.value = item; dialogVisible.value = true }

const getRec = async () => {
  if (!form.value.userId.trim()) return ElMessage.warning('请输入用户ID')
  loading.value = true
  searched.value = true
  try {
    const { data } = await getRecommendations(form.value.userId, form.value.topK)
    list.value = data.recommendations || []
    scores.value = data.scores || []
  } catch (e) {
    ElMessage.error('获取失败')
  } finally {
    loading.value = false
  }
}
</script>
