<template>
  <div>
    <div class="page-card">
      <div class="card-header"><h3>智能推荐</h3></div>
      <div class="card-body">
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
        <div v-if="!loading && searched && !list.length" style="margin-top:12px;color:#909399;font-size:13px">
          暂无推荐内容，请先在 AI 对话中发送一些消息
        </div>
      </div>
    </div>

    <el-row :gutter="16" v-if="list.length" style="margin-top:16px">
      <el-col :span="8" v-for="(item, i) in list" :key="i">
        <div class="rec-card">
          <div class="rec-header">
            <div class="rec-icon" :style="{ background: colors[i % 5] }">{{ icons[item.type] || '📌' }}</div>
            <div class="rec-score" v-if="scores[i]">{{ (scores[i] * 100).toFixed(0) }}%</div>
          </div>
          <div class="rec-title">{{ item.title }}</div>
          <div class="rec-type">类型：{{ item.type }}</div>
          <el-button type="primary" text size="small" @click="showDetail(item)">查看详情 →</el-button>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="推荐详情" width="600px">
      <div v-if="detailItem">
        <h4 style="margin:0 0 12px">用户对话</h4>
        <div style="background:#f5f7fa;padding:12px;border-radius:6px;line-height:1.8;color:#303133;white-space:pre-wrap">{{ detailItem.full_text }}</div>

        <div v-if="detailItem.related && detailItem.related.length" style="margin-top:16px">
          <h4 style="margin:0 0 12px">相关知识库内容</h4>
          <div v-for="(r, i) in detailItem.related" :key="i" style="background:#f0f9eb;padding:12px;border-radius:6px;margin-bottom:8px">
            <div style="font-size:12px;color:#67c23a;margin-bottom:4px">相似度 {{ (1 - r.score) * 100 }}%</div>
            <div style="color:#303133;line-height:1.6">{{ r.content }}</div>
          </div>
        </div>

        <div v-if="!detailItem.related || !detailItem.related.length" style="margin-top:16px;color:#909399;font-size:13px">
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

<style scoped>
.rec-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: all 0.2s;
}
.rec-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.rec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rec-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.rec-score { font-size: 24px; font-weight: 700; color: #409eff; }
.rec-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.rec-type { font-size: 12px; color: #909399; margin-bottom: 8px; }
</style>
