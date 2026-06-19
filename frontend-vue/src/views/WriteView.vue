<template>
  <div class="write-page">
    <el-row :gutter="16" style="height:100%">
      <!-- 左侧输入 -->
      <el-col :span="10">
        <div class="page-card" style="height:100%">
          <div class="card-header"><h3>AI 写作</h3></div>
          <div class="card-body">
            <el-form label-position="top">
              <el-form-item label="文章主题">
                <el-input v-model="form.topic" placeholder="例如：人工智能在医疗领域的应用" />
              </el-form-item>
              <el-form-item label="写作风格">
                <el-radio-group v-model="form.style">
                  <el-radio-button value="专业分析">专业分析</el-radio-button>
                  <el-radio-button value="科普文章">科普文章</el-radio-button>
                  <el-radio-button value="新闻报道">新闻报道</el-radio-button>
                  <el-radio-button value="产品文案">产品文案</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="文章长度">
                <el-radio-group v-model="form.length">
                  <el-radio-button value="short">短篇</el-radio-button>
                  <el-radio-button value="medium">中篇</el-radio-button>
                  <el-radio-button value="long">长篇</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="补充说明（可选）">
                <el-input v-model="form.extra" type="textarea" :rows="3" placeholder="其他要求..." />
              </el-form-item>
              <el-button type="primary" :loading="loading" @click="generate" style="width:100%">
                <span v-if="!loading">✨ 开始生成</span>
                <span v-else>生成中...</span>
              </el-button>
            </el-form>
          </div>
        </div>
      </el-col>

      <!-- 右侧结果 -->
      <el-col :span="14">
        <div class="page-card" style="height:100%">
          <div class="card-header">
            <h3>生成结果</h3>
            <div v-if="result" style="display:flex;gap:8px">
              <el-tag size="small">{{ result.word_count }} 字</el-tag>
              <el-tag size="small" type="success">{{ result.reading_time }}</el-tag>
              <el-button size="small" @click="copy">复制</el-button>
            </div>
          </div>
          <div class="card-body" style="overflow-y:auto">
            <div v-if="!result" class="empty-state">
              <div style="font-size:48px;margin-bottom:12px">✍️</div>
              <p style="color:#909399">输入主题后点击生成</p>
            </div>
            <div v-else class="result-content" v-html="result.content"></div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { generateContent } from '../api'
import { ElMessage } from 'element-plus'

const form = ref({ topic: '', style: '专业分析', length: 'medium', extra: '' })
const loading = ref(false)
const result = ref(null)

const generate = async () => {
  if (!form.value.topic.trim()) return ElMessage.warning('请输入文章主题')
  loading.value = true
  try {
    const { data } = await generateContent(form.value.topic, form.value.style, form.value.length)
    result.value = data
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    loading.value = false
  }
}

const copy = () => {
  if (result.value) {
    navigator.clipboard.writeText(result.value.content)
    ElMessage.success('已复制')
  }
}
</script>

<style scoped>
.write-page { height: calc(100vh - 100px); }
.empty-state { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.result-content { line-height: 1.8; font-size: 14px; color: #303133; white-space: pre-wrap; }
</style>
