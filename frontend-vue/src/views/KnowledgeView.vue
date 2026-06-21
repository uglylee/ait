<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="8">
        <div class="page-card">
          <div class="card-header">
            <h3>知识库</h3>
            <el-tag type="info" size="small">ChromaDB</el-tag>
          </div>
          <div class="card-body">
            <div v-if="loading" style="text-align:center;padding:40px 0">
              <el-icon class="is-loading" :size="24"><Loading /></el-icon>
              <p style="color:#909399;margin-top:8px">加载中...</p>
            </div>
            <div v-else>
              <div class="stat-row">
                <span class="stat-label">文档片段</span>
                <span class="stat-value">{{ stats.total_chunks || 0 }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">状态</span>
                <el-tag :type="statusOk ? 'success' : 'danger'" size="small">{{ statusOk ? '就绪' : '异常' }}</el-tag>
              </div>
              <el-button type="danger" size="small" style="width:100%;margin-top:8px" :loading="clearing" @click="clearKB" :disabled="!stats.total_chunks">
                清空知识库
              </el-button>

              <el-divider />

              <h4 style="margin:0 0 12px">添加文档</h4>
              <el-upload
                ref="uploadRef"
                drag
                multiple
                :auto-upload="false"
                :on-change="handleFileChange"
                :before-upload="() => false"
                accept=".txt,.pdf,.csv,.md,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.html,.htm,.json,.xml,.log"
              >
                <el-icon :size="40" style="color:#909399"><UploadFilled /></el-icon>
                <div style="margin-top:8px;color:#606266">拖拽文件到此处，或<em>点击上传</em></div>
                <div style="font-size:12px;color:#909399;margin-top:4px">支持批量上传：PDF Word Excel PPT TXT CSV HTML Markdown JSON XML</div>
              </el-upload>
              <div v-if="pendingFiles.length" style="margin-top:8px;font-size:12px;color:#606266">
                已选择 {{ pendingFiles.length }} 个文件
              </div>
              <el-button type="primary" style="width:100%;margin-top:12px" :loading="uploading" @click="uploadFile" :disabled="!pendingFiles.length">
                {{ uploading ? uploadProgress : '上传到知识库' }}
              </el-button>

              <el-divider />

              <h4 style="margin:0 0 12px">添加文本</h4>
              <el-input v-model="addText" type="textarea" :rows="3" placeholder="输入文本内容..." />
              <el-button type="primary" style="width:100%;margin-top:8px" :loading="adding" @click="addTextToKB" :disabled="!addText.trim()">
                添加到知识库
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="16">
        <div class="page-card" style="height:100%">
          <div class="card-header">
            <h3>知识检索</h3>
          </div>
          <div class="card-body" style="display:flex;flex-direction:column">
            <el-input v-model="query" placeholder="输入问题检索知识库..." @keydown.enter="search" style="margin-bottom:16px">
              <template #append>
                <el-button :loading="searching" @click="search">检索</el-button>
              </template>
            </el-input>
            <div style="margin-bottom:12px">
              <el-switch v-model="useAI" active-text="AI 回答" inactive-text="仅检索" />
            </div>
            <div v-if="searchError" style="margin-bottom:12px">
              <el-alert :title="searchError" type="error" show-icon :closable="false" />
            </div>
            <div v-if="ragAnswer" class="rag-answer">
              <div class="answer-label">AI 回答</div>
              <div>{{ ragAnswer }}</div>
            </div>
            <div style="flex:1;overflow-y:auto">
              <div v-if="!results.length && !searching && !ragAnswer" class="empty-state">
                <p style="color:#909399">输入问题后按 Enter 检索</p>
              </div>
              <div v-for="(r, i) in results" :key="i" class="search-result">
                <div class="result-score">{{ (r.score * 100).toFixed(0) }}%</div>
                <div class="result-content">
                  <div class="result-source">
                    片段 {{ i + 1 }}
                    <span v-if="r.file_name" style="margin-left:8px">
                      <el-tag size="small" type="info">{{ r.file_name }}</el-tag>
                      <a v-if="r.file_name" :href="ragDownloadFile(r.file_id)" target="_blank" style="margin-left:4px;font-size:12px;color:#409eff;text-decoration:none">下载</a>
                    </span>
                  </div>
                  <div class="result-text">{{ r.content }}</div>
                </div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, UploadFilled } from '@element-plus/icons-vue'
import { ragStatus, ragAddText, ragAddFiles, ragQuery, ragClear, ragDownloadFile } from '../api'

const loading = ref(true)
const stats = ref({})
const statusOk = ref(false)
const uploadRef = ref(null)
const clearing = ref(false)

const pendingFiles = ref([])
const uploading = ref(false)
const uploadProgress = ref('')
const addText = ref('')
const adding = ref(false)

const query = ref('')
const searching = ref(false)
const results = ref([])
const ragAnswer = ref('')
const searchError = ref('')
const useAI = ref(false)

const clearKB = async () => {
  try {
    await ElMessageBox.confirm(`确定要清空知识库吗？将删除全部 ${stats.value.total_chunks || 0} 个文档片段，此操作不可恢复。`, '清空知识库', { type: 'warning', confirmButtonText: '确定清空', cancelButtonText: '取消' })
    clearing.value = true
    await ragClear()
    stats.value = {}
    results.value = []
    ragAnswer.value = ''
    ElMessage.success('知识库已清空')
    await fetchStatus()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('清空失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    clearing.value = false
  }
}

const fetchStatus = async () => {
  loading.value = true
  try {
    const res = await ragStatus()
    stats.value = res.data.rag_stats || {}
    statusOk.value = !!res.data.features
  } catch (e) {
    statusOk.value = false
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file, fileList) => {
  pendingFiles.value = fileList.map(f => f.raw)
}

const uploadFile = async () => {
  if (!pendingFiles.value.length) return
  uploading.value = true
  try {
    let totalChunks = 0
    for (let i = 0; i < pendingFiles.value.length; i++) {
      uploadProgress.value = `上传中 (${i + 1}/${pendingFiles.value.length})...`
      const res = await ragAddFiles([pendingFiles.value[i]])
      totalChunks += res.data.chunks_added || 0
    }
    ElMessage.success(`上传成功，新增 ${totalChunks} 个片段`)
    pendingFiles.value = []
    uploadRef.value?.clearFiles()
    await fetchStatus()
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
    uploadProgress.value = ''
  }
}

const addTextToKB = async () => {
  if (!addText.value.trim()) return
  adding.value = true
  try {
    const res = await ragAddText(addText.value)
    ElMessage.success(`添加成功，新增 ${res.data.chunks_added} 个片段`)
    addText.value = ''
    stats.value = res.data.stats || {}
  } catch (e) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    adding.value = false
  }
}

const search = async () => {
  if (!query.value.trim()) return
  searching.value = true
  results.value = []
  ragAnswer.value = ''
  searchError.value = ''
  try {
    const res = await ragQuery(query.value, 3, null, useAI.value)
    ragAnswer.value = res.data.answer || ''
    results.value = res.data.sources || []
    if (!results.value.length && !ragAnswer.value) {
      searchError.value = '知识库中暂无相关内容'
    }
  } catch (e) {
    searchError.value = '检索失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    searching.value = false
  }
}

onMounted(fetchStatus)
</script>

<style scoped>
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}
.stat-label { color: #606266; font-size: 14px; }
.stat-value { color: #303133; font-size: 18px; font-weight: 600; }
.rag-answer {
  padding: 16px;
  background: #f0f9eb;
  border-radius: 8px;
  margin-bottom: 16px;
  line-height: 1.6;
}
.answer-label {
  font-size: 12px;
  color: #67c23a;
  font-weight: 600;
  margin-bottom: 8px;
}
.empty-state { height: 200px; display: flex; align-items: center; justify-content: center; }
.search-result {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  background: #f8f9fa;
}
.result-score {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
.result-source { font-size: 12px; color: #909399; margin-bottom: 4px; }
.result-text { font-size: 14px; color: #303133; line-height: 1.6; }
</style>
