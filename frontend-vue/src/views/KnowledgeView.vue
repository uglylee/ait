<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- Left: KB Management -->
      <div class="lg:col-span-2">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-800">知识库</h3>
            <span class="text-[10px] font-medium text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">ChromaDB</span>
          </div>
          <div class="p-5">
            <div v-if="loading" class="text-center py-10">
              <div class="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="text-gray-400 text-sm mt-2">加载中...</p>
            </div>
            <div v-else>
              <!-- Stats -->
              <div class="flex justify-between items-center py-2.5 border-b border-gray-50">
                <span class="text-sm text-gray-500">文档片段</span>
                <span class="text-lg font-bold text-gray-800">{{ stats.total_chunks || 0 }}</span>
              </div>
              <div class="flex justify-between items-center py-2.5">
                <span class="text-sm text-gray-500">状态</span>
                <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', statusOk ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500']">
                  {{ statusOk ? '就绪' : '异常' }}
                </span>
              </div>

              <!-- Clear Button -->
              <button
                :disabled="!stats.total_chunks || clearing"
                :class="['w-full mt-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  (!stats.total_chunks || clearing) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-red-50 text-red-500 hover:bg-red-100 hover:shadow-sm active:scale-[0.98]']"
                @click="clearKB"
              >
                <span v-if="clearing" class="inline-block w-3.5 h-3.5 border-2 border-red-400 border-t-transparent rounded-full animate-spin mr-1.5 align-middle"></span>
                {{ clearing ? '清空中...' : '🗑️ 清空知识库' }}
              </button>

              <div class="my-4 border-t border-gray-100"></div>

              <!-- Upload -->
              <h4 class="text-sm font-semibold text-gray-700 mb-3">📄 添加文档</h4>
              <el-upload
                ref="uploadRef"
                drag
                multiple
                :auto-upload="false"
                :on-change="handleFileChange"
                :before-upload="() => false"
                accept=".txt,.pdf,.csv,.md,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.html,.htm,.json,.xml,.log"
              >
                <div class="py-4">
                  <div class="text-4xl mb-2">☁️</div>
                  <div class="text-sm text-gray-500">拖拽文件到此处，或 <span class="text-indigo-500 font-medium">点击上传</span></div>
                  <div class="text-[11px] text-gray-300 mt-1.5">PDF Word Excel PPT TXT CSV HTML Markdown JSON XML</div>
                </div>
              </el-upload>
              <div v-if="pendingFiles.length" class="mt-2 flex items-center gap-1.5 text-xs text-indigo-500">
                <span class="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                已选择 {{ pendingFiles.length }} 个文件
              </div>
              <button
                :disabled="!pendingFiles.length || uploading"
                :class="['w-full mt-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  (!pendingFiles.length || uploading) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-indigo-500 text-white hover:bg-indigo-600 shadow-md shadow-indigo-200 hover:shadow-lg hover:shadow-indigo-300 hover:-translate-y-0.5 active:scale-[0.98]']"
                @click="uploadFile"
              >
                <span v-if="uploading" class="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin mr-1.5 align-middle"></span>
                {{ uploading ? uploadProgress : '⬆️ 上传到知识库' }}
              </button>

              <div class="my-4 border-t border-gray-100"></div>

              <!-- Text Input -->
              <h4 class="text-sm font-semibold text-gray-700 mb-3">📝 添加文本</h4>
              <el-input v-model="addText" type="textarea" :rows="3" placeholder="输入文本内容..." />
              <button
                :disabled="!addText.trim() || adding"
                :class="['w-full mt-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  (!addText.trim() || adding) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-violet-500 text-white hover:bg-violet-600 shadow-md shadow-violet-200 hover:shadow-lg hover:shadow-violet-300 hover:-translate-y-0.5 active:scale-[0.98]']"
                @click="addTextToKB"
              >
                <span v-if="adding" class="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin mr-1.5 align-middle"></span>
                {{ adding ? '添加中...' : '✨ 添加到知识库' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Search -->
      <div class="lg:col-span-3">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 h-full flex flex-col">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-800">🔍 知识检索</h3>
          </div>
          <div class="p-5 flex flex-col flex-1">
            <!-- Search Input -->
            <div class="flex gap-2 mb-4">
              <el-input v-model="query" placeholder="输入问题检索知识库..." @keydown.enter="search" class="flex-1" />
              <button
                :disabled="!query.trim() || searching"
                :class="['px-5 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-1.5 flex-shrink-0',
                  (!query.trim() || searching) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-indigo-500 text-white hover:bg-indigo-600 shadow-md shadow-indigo-200 hover:shadow-lg active:scale-[0.98]']"
                @click="search"
              >
                <span v-if="searching" class="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span v-else>🔎</span>
                {{ searching ? '检索中...' : '检索' }}
              </button>
            </div>

            <!-- AI Toggle -->
            <div class="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-xl">
              <el-switch v-model="useAI" />
              <span class="text-xs font-medium" :class="useAI ? 'text-indigo-500' : 'text-gray-400'">AI 回答</span>
              <span v-if="useAI" class="ml-auto text-[10px] text-indigo-400 bg-indigo-50 px-2 py-0.5 rounded-full">会调用 LLM</span>
            </div>

            <!-- Error -->
            <div v-if="searchError" class="mb-3 p-3 bg-red-50 rounded-xl text-sm text-red-500 flex items-center gap-2">
              <span>⚠️</span> {{ searchError }}
            </div>

            <!-- AI Answer -->
            <div v-if="ragAnswer" class="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl mb-4 border border-green-100">
              <div class="text-xs text-green-600 font-semibold mb-2 flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                AI 回答
              </div>
              <div class="text-sm text-gray-700 leading-relaxed">{{ ragAnswer }}</div>
            </div>

            <!-- Results -->
            <div class="flex-1 overflow-y-auto">
              <div v-if="!results.length && !searching && !ragAnswer" class="h-[200px] flex flex-col items-center justify-center text-gray-300">
                <div class="text-4xl mb-3">📚</div>
                <p class="text-sm">输入问题后按 Enter 检索</p>
              </div>
              <div v-for="(r, i) in results" :key="i" class="flex gap-3 p-3.5 rounded-xl bg-gray-50 mb-2 hover:bg-gray-100 transition-colors">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm">
                  {{ (r.score * 100).toFixed(0) }}%
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-xs text-gray-400 mb-1.5 flex items-center gap-1.5">
                    <span>片段 {{ i + 1 }}</span>
                    <span v-if="r.file_name" class="inline-flex items-center gap-1">
                      <span class="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span class="bg-indigo-50 text-indigo-500 px-1.5 py-0.5 rounded text-[10px] font-medium">{{ r.file_name }}</span>
                      <a :href="ragDownloadFile(r.file_id)" target="_blank" class="text-indigo-400 hover:text-indigo-600 underline ml-0.5">下载</a>
                    </span>
                  </div>
                  <div class="text-sm text-gray-600 leading-relaxed">{{ r.content }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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
